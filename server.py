from flask import Flask, request, jsonify, send_from_directory
import requests as http_requests
import os, json, traceback
from datetime import datetime
from pathlib import Path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "4"

app = Flask(__name__, static_folder='.')
app.secret_key = os.environ.get("FLASK_SECRET") or os.urandom(24)

API_KEY      = os.environ.get("CMU_API_KEY")
if not API_KEY:
    raise SystemExit("Set CMU_API_KEY (see .env.example) before starting the server.")
CMU_URL      = os.environ.get("LLM_URL", "https://ai-gateway.andrew.cmu.edu/v1/messages")
MODEL        = "claude-sonnet-4-20250514-v1:0"
SESSIONS_DIR = Path("./sessions")
SESSIONS_DIR.mkdir(exist_ok=True)
Path("./uploads_tmp").mkdir(exist_ok=True)
Path("./exports").mkdir(exist_ok=True)

_indexer = None

def get_indexer():
    global _indexer
    if _indexer is None:
        try:
            from indexer import PDFIndexer
            _indexer = PDFIndexer()
            _indexer.load_index("./rag_index")
            print("[RAG] Indexer loaded")
        except Exception as e:
            print(f"[RAG] Could not load: {e}")
    return _indexer

def claude_call(messages, max_tokens=2000):
    r = http_requests.post(CMU_URL, headers={
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01"
    }, json={"model": MODEL, "max_tokens": max_tokens, "messages": messages}, timeout=60)
    result = r.json()
    if "error" in result:
        print(f"[API ERROR] {result['error']}")
    return result

# ── STATIC ──
@app.route('/')
def index():  return send_from_directory('.', 'index.html')
@app.route('/chat')
def chat():   return send_from_directory('.', 'chat.html')
@app.route('/dev')
def dev():    return send_from_directory('.', 'dev.html')

# ── CLAUDE PROXY ──
@app.route('/api/claude', methods=['POST'])
def claude():
    data = request.json
    try:
        result = claude_call(data.get("messages", []), data.get("max_tokens", 2000))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── SESSION SAVE / LOAD ──
@app.route('/api/session/save', methods=['POST'])
def save_session():
    data = request.json
    sid  = data.get("session_id") or f"initialization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    data["session_id"] = sid
    data["saved_at"]   = datetime.now().isoformat()
    path = SESSIONS_DIR / f"{sid}.json"
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"[SESSION] Saved: {path}")
    return jsonify({"ok": True, "session_id": sid})

@app.route('/api/session/load/<session_id>', methods=['GET'])
def load_session(session_id):
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return jsonify({"error": "not found"}), 404
    with open(path) as f:
        return jsonify(json.load(f))

@app.route('/api/session/list', methods=['GET'])
def list_sessions():
    sessions = []
    for p in sorted(SESSIONS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(p) as f:
                d = json.load(f)
            sessions.append({
                "session_id": p.stem,
                "saved_at": d.get("saved_at", ""),
                "archetype_name": d.get("archetype_name", "Unknown"),
            })
        except: pass
    return jsonify(sessions)

# ── FACULTY AGENT ──
@app.route('/api/faculty', methods=['POST'])
def faculty():
    data       = request.json
    node       = data.get("node", {})
    answers    = data.get("answers", [])
    session_id = data.get("session_id", "")

    domain    = node.get("domain", "purpose")
    node_type = node.get("type", "leaf")

    voices = {
        "creative":     ("The Artist Voice",    "You are a creative mentor. Speak in images and possibility. Ask questions that unlock. 3-4 short paragraphs."),
        "career":       ("The Strategist Voice","You are a pragmatic strategist. Speak directly, give concrete next steps. Do not flatter. 3-4 short paragraphs."),
        "purpose":      ("The Socratic Voice",  "You are a Socratic questioner. Ask the question under the question. End with 2 questions."),
        "identity":     ("The Mirror Voice",    "Show the person what they already know but have not said out loud. Warm, direct, precise. 3-4 paragraphs."),
        "relationship": ("The Connector Voice", "You understand loneliness and belonging. Speak about the need for the right people. 3-4 paragraphs."),
        "action":       ("The Pragmatist Voice","You are direct. Break the unlived thing into smallest first move. 3 paragraphs with one concrete action.")
    }
    vname, vsystem = voices.get(domain if node_type != "action" else "action", voices["purpose"])
    context = "\n".join([f"Q{i+1}: {a['answer']}" for i, a in enumerate(answers)])
    prompt  = f"{vsystem}\n\nContext:\n{context}\n\nExploring: \"{node.get('label','')}\"\nTheir words: \"{node.get('source_quote','')}\"\n\nRespond as {vname}. Be specific. No em dashes."

    try:
        result = claude_call([{"role": "user", "content": prompt}], 800)
        text   = result.get("content", [{}])[0].get("text", "The mentor is gathering thoughts.")
    except Exception as e:
        text = f"Error: {e}"

    # Persist into session file
    if session_id:
        path = SESSIONS_DIR / f"{session_id}.json"
        if path.exists():
            with open(path) as f:
                sess = json.load(f)
            sess.setdefault("faculty_responses", {})[node.get("id","")] = {
                "voice": vname, "response": text, "ts": datetime.now().isoformat()
            }
            with open(path, 'w') as f:
                json.dump(sess, f, indent=2)

    return jsonify({"voice": vname, "response": text})

# ── RAG QUERY ──
@app.route('/api/rag/query', methods=['POST'])
def rag_query():
    data     = request.json
    question = data.get("question", "")
    top_k    = int(data.get("top_k", 4))
    model    = data.get("model", None)
    pfilter  = data.get("paper_filter", None)
    lang     = data.get("language", "English")
    max_iter = int(data.get("max_iterations", 2))

    ix = get_indexer()
    if ix is None:
        return jsonify({"error": "RAG not available. Index documents via /dev first."}), 503
    try:
        answer, sources = ix.query(question, top_k=top_k, model=model,
                                   paper_filter=pfilter, output_language=lang,
                                   max_iterations=max_iter)
        srcs = [{"source": s.get("source",""), "page": s.get("page",0),
                 "paper_type": s.get("paper_type",""), "text": s.get("text","")[:300]}
                for s in (sources or [])]
        return jsonify({"answer": answer, "sources": srcs})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route('/api/rag/stats', methods=['GET'])
def rag_stats():
    ix = get_indexer()
    if ix is None:
        return jsonify({"status": "not_loaded", "chunks": 0, "collection": "", "index_type": ""})
    try:
        ix._collection.load()
        return jsonify({"status": "loaded", "chunks": ix._collection.num_entities,
                        "collection": ix.collection_name, "index_type": ix.index_type})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# ── DEV: INDEX ──
@app.route('/api/scrape', methods=['POST'])
def scrape():
    """Scrape public info about a person from name + links."""
    data = request.json
    name   = data.get("name", "")
    github = data.get("github", "")
    links  = data.get("links", [])

    gathered = []

    # GitHub API — free, no key needed
    if github:
        handle = github.strip().lstrip("https://github.com/").strip("/").split("/")[0]
        try:
            r = http_requests.get(f"https://api.github.com/users/{handle}", timeout=8)
            if r.status_code == 200:
                u = r.json()
                gathered.append(f"GitHub: {u.get('name','')} — {u.get('bio','')} — {u.get('public_repos',0)} repos — {u.get('followers',0)} followers — Location: {u.get('location','')} — Blog: {u.get('blog','')}")
            # Top repos
            r2 = http_requests.get(f"https://api.github.com/users/{handle}/repos?sort=stars&per_page=5", timeout=8)
            if r2.status_code == 200:
                repos = r2.json()
                for repo in repos[:5]:
                    gathered.append(f"Repo: {repo.get('name','')} — {repo.get('description','')} — Stars: {repo.get('stargazers_count',0)} — Language: {repo.get('language','')}")
        except: pass

    # Scrape any provided links (resume, portfolio, LinkedIn public)
    for link in links[:3]:
        if not link.strip(): continue
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = http_requests.get(link.strip(), timeout=8, headers=headers)
            if r.status_code == 200:
                # Extract text — strip HTML tags roughly
                import re as _re
                text = _re.sub(r'<[^>]+>', ' ', r.text)
                text = _re.sub(r'\s+', ' ', text).strip()[:2000]
                gathered.append(f"From {link}: {text}")
        except: pass

    return jsonify({"gathered": gathered, "name": name})


@app.route('/api/websearch', methods=['POST'])
def websearch():
    query = request.json.get("query", "")
    if not query:
        return jsonify({"results": []})
    try:
        r = http_requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=8, headers={"User-Agent": "Mozilla/5.0"}
        )
        data = r.json()
        results = []
        if data.get("AbstractText"):
            results.append({"title": data.get("Heading",""), "snippet": data["AbstractText"], "url": data.get("AbstractURL","")})
        for item in data.get("RelatedTopics", [])[:4]:
            if isinstance(item, dict) and item.get("Text"):
                results.append({"snippet": item.get("Text",""), "url": item.get("FirstURL","")})
        return jsonify({"results": results[:5]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})


@app.route('/api/dev/index', methods=['POST'])
def dev_index():
    global _indexer
    from indexer import PDFIndexer
    index_type = request.form.get("index_type", "HNSW")
    chunk_size = int(request.form.get("chunk_size", 256))
    paper_type = request.form.get("paper_type", "Other")
    url        = request.form.get("url", "")
    drop_old   = request.form.get("drop_old", "false").lower() == "true"
    files      = request.files.getlist("pdfs")
    if not files:
        return jsonify({"error": "No PDFs uploaded"}), 400
    saved = []
    for f in files:
        p = Path("./uploads_tmp") / f.filename
        f.save(p); saved.append(str(p))
    try:
        if _indexer is None or drop_old:
            _indexer = PDFIndexer(index_type=index_type, chunk_words=chunk_size)
        fmap = {Path(p).name: url for p in saved} if url else {}
        stats = _indexer.index_pdfs(pdf_paths=saved, paper_type=paper_type,
                                    file_url_map=fmap, drop_old=drop_old)
        _indexer.save_index("./rag_index")
        return jsonify({"ok": True, "stats": stats})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route('/api/dev/clear', methods=['POST'])
def dev_clear():
    global _indexer
    if _indexer:
        try:
            _indexer.clear_collection(drop=True)
            _indexer = None
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True})

@app.route('/api/dev/export', methods=['GET'])
def dev_export():
    ix = get_indexer()
    if ix is None:
        return jsonify({"error": "no indexer"}), 503
    out = f"./exports/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.npz"
    n   = ix.export_to_npz(out)
    return jsonify({"ok": True, "path": out, "chunks": n})

if __name__ == '__main__':
    print("\n  → App:  http://127.0.0.1:8501")
    print("  → Chat: http://127.0.0.1:8501/chat")
    print("  → Dev:  http://127.0.0.1:8501/dev\n")
    app.run(port=8501, debug=False, threaded=True)
