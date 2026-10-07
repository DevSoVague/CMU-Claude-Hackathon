"""
RAG indexer for The Latent Map (/chat and /dev).

PDFs are split into word-window chunks, embedded locally with
sentence-transformers, stored in Milvus, and answered with Claude through the
public Anthropic Messages API. Milvus Lite (a local file) is used by default,
so no Milvus server is required for local runs.

Environment variables (all optional except ANTHROPIC_API_KEY for answers):
  ANTHROPIC_API_KEY   Anthropic key used for answer generation
  ANTHROPIC_MODEL     Claude model id (default: same model as server.py)
  MILVUS_URI          Milvus endpoint, e.g. http://localhost:19530.
                      Default: ./rag_index/milvus_lite.db (Milvus Lite)
  MILVUS_TOKEN        Milvus token (Zilliz Cloud / auth-enabled Milvus)
  MILVUS_COLLECTION   Collection name (default: latent_map_rag)
  EMBED_MODEL         sentence-transformers model
                      (default: sentence-transformers/all-MiniLM-L6-v2)
  EMBED_DEVICE        cpu | mps | cuda (default: cpu)

Interface used by server.py:
  PDFIndexer(index_type="HNSW", chunk_words=256)
  .index_pdfs(pdf_paths, paper_type, file_url_map, drop_old) -> dict
  .save_index(dir) / .load_index(dir)
  .query(question, top_k, model, paper_filter, output_language, max_iterations)
      -> (answer, sources)
  .clear_collection(drop=True)
  .export_to_npz(path) -> int
  ._collection, .collection_name, .index_type
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

DEFAULT_INDEX_DIR = "./rag_index"
MILVUS_URI = os.environ.get("MILVUS_URI", "")
MILVUS_TOKEN = os.environ.get("MILVUS_TOKEN", "")
MILVUS_ALIAS = "latent_map"
DEFAULT_COLLECTION = os.environ.get("MILVUS_COLLECTION", "latent_map_rag")

EMBED_MODEL = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBED_DEVICE = os.environ.get("EMBED_DEVICE", "cpu")

INDEX_TYPES = ["HNSW", "IVF_PQ", "DiskANN"]
META_FILE = "index_meta.json"

_EMBEDDER = None


def _get_embedder():
    """Load the sentence-transformers model once per process."""
    global _EMBEDDER
    if _EMBEDDER is None:
        from sentence_transformers import SentenceTransformer
        _EMBEDDER = SentenceTransformer(EMBED_MODEL, device=EMBED_DEVICE)
    return _EMBEDDER


def _milvus_uri(index_dir: str) -> str:
    if MILVUS_URI:
        return MILVUS_URI
    Path(index_dir).mkdir(parents=True, exist_ok=True)
    return str(Path(index_dir) / "milvus_lite.db")


class PDFIndexer:
    def __init__(
        self,
        index_type: str = "HNSW",
        chunk_words: int = 256,
        overlap_words: int = 40,
        collection_name: str = DEFAULT_COLLECTION,
        index_dir: str = DEFAULT_INDEX_DIR,
    ):
        if index_type not in INDEX_TYPES:
            raise ValueError(f"index_type must be one of {INDEX_TYPES}")
        self.index_type = index_type
        self.chunk_words = max(32, int(chunk_words))
        self.overlap_words = min(overlap_words, self.chunk_words // 4)
        self.collection_name = collection_name
        self.index_dir = index_dir
        self.embedding_dim: Optional[int] = None
        self._collection: Optional[Collection] = None
        self._connected = False

    # ── Milvus ───────────────────────────────────────────────────────────────
    def _connect(self) -> None:
        if self._connected:
            return
        kwargs = {"alias": MILVUS_ALIAS, "uri": _milvus_uri(self.index_dir)}
        if MILVUS_TOKEN:
            kwargs["token"] = MILVUS_TOKEN
        connections.connect(**kwargs)
        self._connected = True

    def _schema(self, dim: int) -> CollectionSchema:
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="chunk_id", dtype=DataType.INT64),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="url", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="page", dtype=DataType.INT64),
            FieldSchema(name="paper_type", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=16384),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        ]
        return CollectionSchema(fields=fields, description="Latent Map RAG chunks")

    def _index_params(self, dim: int) -> Dict:
        if self.index_type == "HNSW":
            return {"index_type": "HNSW", "metric_type": "COSINE",
                    "params": {"M": 32, "efConstruction": 200}}
        if self.index_type == "IVF_PQ":
            m = next(k for k in (16, 8, 4, 2, 1) if dim % k == 0)
            return {"index_type": "IVF_PQ", "metric_type": "COSINE",
                    "params": {"nlist": 128, "m": m, "nbits": 8}}
        return {"index_type": "DISKANN", "metric_type": "COSINE", "params": {}}

    def _search_params(self) -> Dict:
        if self.index_type == "HNSW":
            return {"metric_type": "COSINE", "params": {"ef": 128}}
        if self.index_type == "IVF_PQ":
            return {"metric_type": "COSINE", "params": {"nprobe": 16}}
        return {"metric_type": "COSINE", "params": {}}

    def _ensure_collection(self, dim: int, drop_old: bool = False) -> None:
        self._connect()
        exists = utility.has_collection(self.collection_name, using=MILVUS_ALIAS)
        if exists and drop_old:
            utility.drop_collection(self.collection_name, using=MILVUS_ALIAS)
            exists = False
        if exists:
            self._collection = Collection(self.collection_name, using=MILVUS_ALIAS)
            return
        self._collection = Collection(
            name=self.collection_name, schema=self._schema(dim),
            using=MILVUS_ALIAS, shards_num=1,
        )
        # Milvus Lite only implements FLAT and silently maps other index types.
        self._collection.create_index("embedding", self._index_params(dim))

    # ── Extraction and chunking ──────────────────────────────────────────────
    @staticmethod
    def _clean(text: str) -> str:
        text = text.replace("\x00", " ")
        text = re.sub(r"-\n(\w)", r"\1", text)
        return re.sub(r"\s+", " ", text).strip()

    def _chunk(self, text: str) -> List[str]:
        words = text.split()
        if not words:
            return []
        step = self.chunk_words - self.overlap_words
        return [" ".join(words[i:i + self.chunk_words])
                for i in range(0, max(len(words) - self.overlap_words, 1), step)]

    def extract_and_chunk(self, pdf_path: str, paper_type: str, url: str = "") -> List[Dict]:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        name = Path(pdf_path).name
        chunks = []
        for page_no, page in enumerate(reader.pages, start=1):
            text = self._clean(page.extract_text() or "")
            for piece in self._chunk(text):
                chunks.append({"source": name, "url": url, "page": page_no,
                               "paper_type": paper_type, "text": piece[:16000]})
        return chunks

    # ── Embedding ────────────────────────────────────────────────────────────
    def _embed(self, texts: List[str]) -> List[List[float]]:
        vecs = _get_embedder().encode(texts, batch_size=32, normalize_embeddings=True,
                                      show_progress_bar=False)
        return [v.tolist() for v in vecs]

    # ── Indexing ─────────────────────────────────────────────────────────────
    def index_pdfs(self, pdf_paths: List[str], paper_type: str = "Other",
                   file_url_map: Optional[Dict[str, str]] = None,
                   drop_old: bool = False) -> Dict:
        file_url_map = file_url_map or {}
        chunks: List[Dict] = []
        per_file = {}
        for p in pdf_paths:
            c = self.extract_and_chunk(p, paper_type, file_url_map.get(Path(p).name, ""))
            per_file[Path(p).name] = len(c)
            chunks.extend(c)
        if not chunks:
            raise ValueError("No extractable text found in the uploaded PDFs.")

        vectors = self._embed([c["text"] for c in chunks])
        self.embedding_dim = len(vectors[0])
        self._ensure_collection(self.embedding_dim, drop_old=drop_old)

        start = self._collection.num_entities
        self._collection.insert([
            [start + i for i in range(len(chunks))],
            [c["source"] for c in chunks],
            [c["url"] for c in chunks],
            [c["page"] for c in chunks],
            [c["paper_type"] for c in chunks],
            [c["text"] for c in chunks],
            vectors,
        ])
        self._collection.flush()
        self._collection.load()
        return {"files": per_file, "chunks_added": len(chunks),
                "total_chunks": self._collection.num_entities,
                "index_type": self.index_type, "collection": self.collection_name,
                "embed_model": EMBED_MODEL, "dim": self.embedding_dim}

    # ── Persistence ──────────────────────────────────────────────────────────
    def save_index(self, directory: str = DEFAULT_INDEX_DIR) -> None:
        Path(directory).mkdir(parents=True, exist_ok=True)
        meta = {"collection_name": self.collection_name, "index_type": self.index_type,
                "chunk_words": self.chunk_words, "embed_model": EMBED_MODEL,
                "embedding_dim": self.embedding_dim}
        (Path(directory) / META_FILE).write_text(json.dumps(meta, indent=2))

    def load_index(self, directory: str = DEFAULT_INDEX_DIR) -> None:
        meta_path = Path(directory) / META_FILE
        if not meta_path.exists():
            raise FileNotFoundError(f"No index metadata at {meta_path}; index PDFs via /dev first.")
        meta = json.loads(meta_path.read_text())
        self.collection_name = meta.get("collection_name", self.collection_name)
        self.index_type = meta.get("index_type", self.index_type)
        self.chunk_words = meta.get("chunk_words", self.chunk_words)
        self.embedding_dim = meta.get("embedding_dim")
        self.index_dir = directory
        self._connect()
        if not utility.has_collection(self.collection_name, using=MILVUS_ALIAS):
            raise FileNotFoundError(f"Milvus collection '{self.collection_name}' not found.")
        self._collection = Collection(self.collection_name, using=MILVUS_ALIAS)
        self._collection.load()

    def clear_collection(self, drop: bool = False) -> None:
        self._connect()
        if not utility.has_collection(self.collection_name, using=MILVUS_ALIAS):
            return
        if drop:
            utility.drop_collection(self.collection_name, using=MILVUS_ALIAS)
            self._collection = None
            meta = Path(self.index_dir) / META_FILE
            if meta.exists():
                meta.unlink()
        else:
            self._collection.delete("chunk_id >= 0")
            self._collection.flush()

    def export_to_npz(self, npz_path: str) -> int:
        import numpy as np
        if self._collection is None:
            raise RuntimeError("No active collection to export.")
        self._collection.load()
        fields = ["chunk_id", "source", "url", "page", "paper_type", "text", "embedding"]
        rows: List[Dict] = []
        total = self._collection.num_entities
        offset = 0
        while offset < total:
            batch = self._collection.query(expr="chunk_id >= 0", output_fields=fields,
                                           offset=offset, limit=1000)
            if not batch:
                break
            rows.extend(batch)
            offset += len(batch)
        Path(npz_path).parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            npz_path,
            chunk_ids=np.array([r["chunk_id"] for r in rows], dtype=np.int64),
            sources=np.array([r["source"] for r in rows], dtype=object),
            urls=np.array([r["url"] for r in rows], dtype=object),
            pages=np.array([r["page"] for r in rows], dtype=np.int64),
            paper_types=np.array([r["paper_type"] for r in rows], dtype=object),
            texts=np.array([r["text"] for r in rows], dtype=object),
            embeddings=np.array([r["embedding"] for r in rows], dtype=np.float32),
            meta=np.array([json.dumps({"collection_name": self.collection_name,
                                       "index_type": self.index_type,
                                       "embed_model": EMBED_MODEL})], dtype=object),
        )
        return len(rows)

    # ── Retrieval + generation ───────────────────────────────────────────────
    def _search(self, question: str, top_k: int, paper_filter: Optional[str]) -> List[Dict]:
        if self._collection is None:
            raise RuntimeError("Index not loaded.")
        expr = None
        if paper_filter and paper_filter not in ("All", "all", "Any"):
            safe = paper_filter.replace('"', "")
            expr = f'paper_type == "{safe}"'
        hits = self._collection.search(
            data=self._embed([question]), anns_field="embedding",
            param=self._search_params(), limit=top_k, expr=expr,
            output_fields=["source", "url", "page", "paper_type", "text"],
        )[0]
        docs = []
        for h in hits:
            ent = h.entity
            docs.append({"source": ent.get("source"), "url": ent.get("url"),
                         "page": ent.get("page"), "paper_type": ent.get("paper_type"),
                         "text": ent.get("text"), "score": float(h.distance)})
        return docs

    @staticmethod
    def _claude(prompt: str, model: str, max_tokens: int = 1200) -> str:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        r = requests.post(ANTHROPIC_URL, headers={
            "Content-Type": "application/json", "x-api-key": key,
            "anthropic-version": "2023-06-01",
        }, json={"model": model, "max_tokens": max_tokens,
                 "messages": [{"role": "user", "content": prompt}]}, timeout=90)
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"Anthropic API error: {data['error']}")
        return "".join(b.get("text", "") for b in data.get("content", [])).strip()

    def query(self, question: str, top_k: int = 4, model: Optional[str] = None,
              paper_filter: Optional[str] = None, output_language: str = "English",
              max_iterations: int = 2) -> Tuple[str, List[Dict]]:
        model = model or DEFAULT_MODEL
        docs = self._search(question, top_k, paper_filter)
        if not docs:
            return "I could not find anything relevant in the indexed documents.", []
        context = "\n\n".join(
            f"[{i}] {d['source']} p.{d['page']} ({d['paper_type']})\n{d['text']}"
            for i, d in enumerate(docs, start=1))
        lang = output_language or "English"
        answer = self._claude(
            "You are a warm, direct mentor helping a student think about their path. "
            "Answer the question using only the context below and cite passages as [n]. "
            "If the context does not cover it, say so plainly.\n"
            f"Write the answer in {lang}.\n\nContext:\n{context}\n\nQuestion: {question}",
            model)
        # Reflect-and-revise loop: one critique per extra iteration.
        for _ in range(max(0, int(max_iterations) - 1)):
            critique = self._claude(
                "Check this answer against the context. Reply with exactly OK if every "
                "claim is supported, otherwise list the unsupported claims.\n\n"
                f"Context:\n{context}\n\nAnswer:\n{answer}", model, max_tokens=400)
            if critique.strip().upper().startswith("OK"):
                break
            answer = self._claude(
                f"Revise the answer so it only states what the context supports. Keep it in {lang} "
                "and keep the [n] citations.\n\n"
                f"Context:\n{context}\n\nIssues:\n{critique}\n\nAnswer:\n{answer}", model)
        return answer, docs
