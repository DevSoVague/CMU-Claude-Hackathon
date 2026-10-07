# The Latent Map: A project on "Latent Space" in AI and the hidden potential of the student.

> *"The bottleneck to human flourishing is not intelligence. It is access to the right guide at the right moment."*
> Inspired by Dario Amodei, *Machines of Loving Grace*

### **Every Response, Every Sentence, Every Paragraph is Personalised to Each Individual's Response**

*We have also integrated a WebScraper, which finds out every publicly available information about You.*

**Built at CMU x Anthropic Claude Builder Club Hackathon, April 2026** · [Run it locally](#running-locally)
Theme: Creative Flourishing

**Team:** Devavrath Sandeep and Haiya Niraj Shah
Masters in Artificial Intelligence Engineering - Biomedical Engineering, Carnegie Mellon University

Google Drive Link to the demo video: https://drive.google.com/file/d/1J3CwH_R8HaT_TTFVMChV4EAe5dPpBXzN/view

---

## What Is This

Most people never discover what they are actually built for. Not because they lack the talent or the drive - but because they never had the right person ask them the right question at the right time.

A brilliant mentor asks the question under the question. They see the pattern you cannot see in yourself. They hold up a mirror that does not flatter.

**Latent Map, our solution gives everyone that mentor.** A psychologically grounded, deeply personalized AI system that interviews you, maps your unlived life, identifies your archetype, and connects you to a counselor and a research base that can actually help.

Remember, this is not a personality quiz, nor is it a not a chatbot. It is a system designed to do one thing: help people understand themselves in a way they have not before - and then do something about it.
---

## Why we came to work on this
- We wondered about what we had missed as we grew up, what were the hobbies and dreams we stopped chasing, and why did we stop them. 
- We realized that there is no module of such in the market which helps us realize what we were.
- This was our driving goal, something completely new, something supporting creativity, and something personal

---

## The Problem We Are Solving

Access to self-understanding is unequal.

The person who gets into IIT or CMU, who builds the company, who finds their calling - they almost always name one thing when you ask how: *a mentor who saw them clearly.* A teacher. A parent. A friend who pushed back.

Most people never get that person. They make decisions based on fear, expectation, and the consensus of whoever is around them. Dario Amodei calls this "herding behavior masquerading as maturity." People accept the default version of their lives because no one ever showed them there was another one.

**Faculty is the equalizer.** It does not replace human mentors. It makes the mentorship that used to require proximity and privilege available to anyone with 20 minutes and a browser.

---

## Who This Is For

- Students deciding what to do with their lives under enormous pressure
- Career changers who feel the pull of an unlived path but cannot name it
- First-generation college students who lack the mentorship networks their peers take for granted
- Counselors and therapists who need richer intake data and a system that remembers
- Coaches and educators who want to personalize their approach at scale
- Anyone who has ever felt that the version of themselves they are living is not the real one

---

## How It Works - The Full Flow

### 1. Intake (60 seconds)

The user provides their name and optionally a GitHub handle, portfolio URL, LinkedIn, or resume link.

In the background, immediately, the server scrapes: GitHub API (bio, top repos, languages, stars, followers) and any provided URLs (portfolio text, resume content, LinkedIn summary). This runs in parallel with the questions. By the time the user finishes answering, their public professional identity has been gathered and woven into every Claude prompt.

The system knows you shipped a RAG system in 2024, that your most starred repo is a computer vision project, that your LinkedIn says "searching for meaningful work." The portrait it generates is not generic. It is about *you*.

---

### 2. The Questions (15 to 20 minutes)

18 questions across two types:

**Psychological depth questions (text):**

Questions designed to surface the things people know but have never said out loud.

- *"What did you want to be at 7, before anyone told you it was unrealistic?"* - surfaces the pre-socialized self
- *"What did you give up that you still think about?"* - surfaces the unlived path
- *"What injustice keeps you up at night?"* - surfaces authentic drive vs. performed values
- *"What do people come to you for, even without asking?"* - surfaces the gift they minimize
- *"What were your past hobbies and why did you stop?"* - surfaces suppression patterns
- *"What are your current hobbies?"* - surfaces what is still alive

These questions are structurally aligned with Narrative Therapy intake protocols. *"What did you give up?"* is a classic externalizing question. *"What do people come to you for?"* is a strengths-based inquiry that bypasses the inner critic. *"The version of me I am most afraid to become"* is a feared-self exercise used in Acceptance and Commitment Therapy.

**Optical illusion and visual instinct questions:**

4 inline SVG illusions (old woman/young lady, duck/rabbit, vase/faces, arrow direction) and 2 visual choice questions (space vs forest, solitude vs friends). What you see first in an ambiguous image is a reliable signal of cognitive style, emotional orientation, and attention bias. These provide additional archetype-matching signal.

**The Emotional Heatmap:**

As each answer is submitted, the text is scanned for emotional valence words. A glowing ambient blob - gold for joy, violet for fear, rose for anger, teal for wonder, sage for peace - slowly appears and drifts behind the questions. By the end, the background is a painting made from the person's emotional fingerprint. No two sessions produce the same background.

---

### 3. The Agentic Pipeline (5 steps, runs after question 18)

All five steps run as sequential Claude API calls, each building on the last.

**Step 1 - Entity Extraction**

Claude reads all 18 answers plus any scraped public profile data and extracts structured entities: unlived dreams with exact quotes, core strengths, core fears, defining moments, recurring themes, unfinished project count, collaboration signals, emotional intensity, world orientation.

This is not summarization. It is semantic decomposition - pulling out the raw material every subsequent step uses.

**Step 2 - Archetype Matching**

Claude receives both the raw answers and the extracted entities and selects from 5 archetypes:

| Archetype | Core Signal |
|---|---|
| The Quiet Fire | Intensity inward. Sees the gap before others do. Made extraordinary and lonely by this. |
| The Reluctant Pioneer | Always ahead of the room. Tired of pioneering alone. Waiting for validation that will not come. |
| The Keeper of Forgotten Things | Drawn to what disappears. Archive is the most valuable thing in the room. |
| The Bridge | Lives between worlds. Contribution, not belonging, is the point. |
| The Seeker (rare) | Unfinished projects everywhere - not from lack of discipline but because the room is always wrong. Searching for the right collaborators. |

The prompt explicitly lists key signals for each archetype and validates the response before using it. A bad API response does not silently default to The Quiet Fire.

**Step 3 - Portrait Personalization**

Claude takes the matched archetype's base portrait template and rewrites it using the person's exact words. "You have spent a long time being careful" becomes grounded in the specific answer they gave in Q2. The portrait references their actual unlived dream, their actual fear, their actual gift.

This is the step that makes people recognize themselves. Not because the writing is beautiful - but because it is accurate.

**Step 4 - Life Graph Generation**

Claude generates a force-directed graph of the person's psychological landscape: a root node (who they are now), branches (major life dimensions), leaf nodes (specific unlived things from their answers with exact quote attribution), and action nodes (one concrete direction per leaf).

The graph renders in D3. Nodes are draggable. Tapping any leaf or action node triggers the Faculty Agent.

**Step 5 - Parallel Background Steps**

- Reflect: one piercing sentence about the person that they know but have never said out loud
- Counselor Brief: a professional summary, key observations, and 3 suggested conversation starters for the human counselor who will see this session

---

### 4. The Faculty Agent (on-demand, per node)

When the user taps a node on the life graph, a server-side call fires to `/api/faculty`. The agent selects a voice based on the node's domain:

| Domain | Voice | What It Does |
|---|---|---|
| Creative | The Artist Voice | Speaks in images and possibility. Opens doors. |
| Career | The Strategist Voice | Direct, pragmatic, concrete next steps. Does not flatter. |
| Purpose | The Socratic Voice | Asks the question under the question. Ends with 2 questions. |
| Identity | The Mirror Voice | Shows the person what they already know but have not said. |
| Relationship | The Connector Voice | Speaks about loneliness, belonging, the need for the right room. |
| Action nodes | The Pragmatist Voice | Breaks the unlived thing into its smallest first move. |

Every response is cached server-side in the session file. Tapping the same node again shows the cached response instantly. The system never forgets what it told you.

---

### 5. Session Persistence

Every session is saved to `sessions/initialization_YYYYMMDD_HHMMSS.json`. The file contains: full answers, archetype and portrait, life graph data, the reflection sentence, all faculty agent responses keyed by node ID, the counselor brief, and scraped public profile context.

On the intro page, previous sessions appear as clickable pills showing archetype name and date. Clicking one restores the full result page - portrait, graph, and cached mentor responses - without re-running the pipeline.

---

### 6. The RAG Chatbot (`/chat`)

After completing the questionnaire, the user opens a chat interface that:

1. Loads their session profile as context
2. Queries a Milvus vector database of indexed research documents
3. Falls back to Claude directly if RAG is unavailable
4. Optionally runs a web search (DuckDuckGo, no key needed) before every query

The profile context toggle sends the portrait and 10 key answers with every query. The web search toggle injects live search results as additional context.

This is where the system becomes a research partner. The person can ask "what does the research say about people who keep abandoning projects?" and get answers grounded in actual indexed papers, filtered through the lens of who they are.

---

### 7. The Dev and Counselor Console (`/dev`)

The admin interface for counselors and parents. Upload PDFs, choose index type (HNSW, IVF_PQ, DiskANN), set chunk size, tag by paper type, add source URLs. View all saved sessions, inspect session JSON, open any session directly in chat.

This is the human-in-the-loop layer. Counselors and parents upload guidelines that shape how the mentor responds. The agent executes their philosophy, not the model's defaults.

---

## How Claude Is Used - For Judges

This section documents every Claude integration point. The linked Google Doc contains screenshots, prompt text, and API call logs.

**Google Doc:** [INSERT LINK]

---

### Integration Point 1 - Entity Extraction (`/api/claude`)

After all 18 answers are submitted, the frontend calls `/api/claude` with a structured extraction prompt. Claude reads the full answer set plus scraped profile data and returns a JSON object of psychological entities.

Example prompt structure:
```
You are a psychologically trained analyst. Extract structured entities from the following interview.

Public profile context: [GitHub bio, top repos, LinkedIn summary if provided]

Answers:
Q1: [answer]
Q2: [answer]
...

Return ONLY valid JSON. No preamble. No markdown fences. Schema:
{
  "unlived_dreams": [{ "label": str, "quote": str, "domain": str }],
  "core_strengths": [str],
  "core_fears": [str],
  "defining_moments": [str],
  "recurring_themes": [str],
  "collaboration_signal": "high" | "medium" | "low",
  "emotional_intensity": "high" | "medium" | "low"
}
```

---

### Integration Point 2 - Archetype Matching (`/api/claude`)

A second Claude call takes the raw answers plus extracted entities and selects one of 5 archetypes. The prompt includes explicit signal descriptions for each archetype to guide the judgment - not a classification task, but a character assessment.

```javascript
fetch('/api/claude', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    messages: [{ role: 'user', content: archetypePrompt }],
    max_tokens: 500
  })
})
```

---

### Integration Point 3 - Portrait Personalization (`/api/claude`)

A third Claude call takes the matched archetype's base portrait template and rewrites it using the person's exact words. The voice instruction: long sentences, no em dashes, no flattery, must reference the person's exact quotes.

---

### Integration Point 4 - Life Graph Generation (`/api/claude`)

A fourth call generates the force-directed graph as JSON. Claude is instructed to think spatially - to map the psychological terrain into nodes, edges, domains, and action vectors, not prose. Output is validated against a schema before rendering. If the response is malformed, the system falls back to a default graph rather than breaking.

---

### Integration Point 5 - Faculty Voices (`/api/faculty`)

Every node tap on the life graph calls `/api/faculty`. The server selects a system prompt based on the node's domain and calls Claude. Each of the 6 voices has a distinct system prompt with specific tone, cadence, and purpose.

Example - The Socratic Voice:
```
You are a Socratic questioner. Ask the question under the question.
End with 2 questions. Be specific. No em dashes.

Context:
[full answer history]

Exploring: "[node label]"
Their words: "[source quote from their answer]"

Respond as The Socratic Voice.
```

Example - The Pragmatist Voice:
```
You are direct. Break the unlived thing into the smallest first move.
3 paragraphs with one concrete action. No em dashes.
```

---

### Integration Point 6 - RAG Chatbot (`/chat`, `/api/rag/query`)

The chatbot sends the full conversation history on every message, with the user's session profile injected as context. When RAG is available, retrieved document chunks are prepended to the user message as grounding context before the Claude call is made.

```javascript
messages: [
  ...conversationHistory,
  { role: 'user', content: ragContext + '\n\n' + userInput }
]
```

---

### Integration Point 7 - Counselor Brief (`/api/claude`)

A final parallel call generates a professional brief for the human counselor. Prompt targets a clinical audience: pattern observations, not diagnoses; key signals, not summaries; three specific conversation starters for the first session.

---

### Model Choices

| Task | Model | Reason |
|---|---|---|
| Archetype matching, portrait, graph | claude-sonnet-4 | Needs psychological depth and nuance |
| Faculty voice responses | claude-sonnet-4 | Voice consistency across sessions matters |
| Counselor brief | claude-haiku | Structured output, lower stakes |
| RAG chat fallback | claude-haiku | Conversational, cost-sensitive |

---

## The Human-in-the-Loop Design

Faculty is not a product that runs autonomously. The architecture is intentional.

**Counselors** upload guidelines that shape mentor behavior through the RAG layer. The agent executes their philosophy, not the model's defaults. If a counselor believes a particular student needs encouragement toward structure, or challenge toward risk, that is configured here.

**Parents** receive thematic summaries rather than transcripts. The mentor shares themes like "exploring questions about creative identity" rather than surfacing raw conversation content. This preserves the trust needed for honest engagement while keeping parents informed.

**Students** interact with the system knowing this layer exists. This is a supported environment, analogous to a school counselor who checks in with parents at the right level of abstraction.

This design directly addresses the core risk of any "think for yourself" tool: without human grounding, the tool's own biases become the new consensus. With humans in the loop, the system amplifies chosen mentors rather than an anonymous model.

---

## The RAG Document Strategy

The Milvus vector store is the difference between a mirror and a map. The mirror shows you who you are. The map shows you where to go.

When someone discovers they are The Seeker - someone who keeps abandoning projects because they cannot find the right collaborators - the natural next question is: *"Is this a real psychological pattern? What does the research say about how people like me find their people?"*

That is a research question. It deserves a research-grounded answer.

The document corpus is organized into 8 categories:

**Identity and Self** - Erikson's identity formation work, Marcia's identity status research (diffusion, foreclosure, moratorium, achievement), Hermans' Dialogical Self Theory, Markus and Nurius on possible selves, McAdams on narrative identity.

**Career and Vocation** - Holland's RIASEC model, Social Cognitive Career Theory, Wrzesniewski's research on calling vs. career vs. job orientations, papers on career regret and the unlived life in occupational psychology.

**Creativity Research** - Csikszentmihalyi's flow research, Amabile on how external evaluation kills creative output, papers on creative self-efficacy, research on adult creativity recovery.

**Loneliness and Belonging** - Cacioppo's loneliness research, cognitive diversity in teams, Brene Brown's belonging vs. fitting-in distinction, Granovetter on weak ties, Edmondson on psychological safety.

**Regret and the Unlived Life** - Gilovich and Medvec on inaction regret dominating long-term, counterfactual thinking research, Jungian frameworks on the unlived life, papers on post-traumatic growth and identity.

**Mentorship Access** - Research on mentorship and first-generation students, the social capital gap, ROI of coaching interventions, informal vs. formal mentorship effectiveness.

**Cultural Context** - Research on bicultural identity, collectivist vs. individualist frameworks, model minority pressure and psychological effects, intergenerational transmission of career expectations.

**Positive Psychology Interventions** - Seligman's PERMA model, strength-based interventions, behavioral activation, implementation intentions, Pennebaker on expressive writing and identity clarity.

Priority indexing order: regret research (Gilovich), flow and creative self-efficacy, loneliness and collaboration research, narrative identity (McAdams), mentorship access research.

---

## Multi-Agent Architecture

The current system uses a sequential pipeline where Claude plays multiple roles. The proposed next evolution is a blackboard architecture where specialized agents share state without calling each other directly.

**Current pipeline:**
```
Intake + Scrape --> Q1..Q18 --> Entity Extraction --> Archetype Match
    --> Portrait --> Graph --> Reflect + Counselor Brief
    --> Node Tap --> Faculty Router --> Faculty Voice
```

**Proposed agents:**

The Observer Agent monitors answers in real time, updating a running psychological model after each submission. By question 10 it has narrowed to 2 likely archetypes. By question 18 the match is nearly deterministic - confirmation rather than discovery.

The Faculty Router evolves from rule-based (domain to voice) to a true routing agent that reads the person's emotional arc across the session. A person processing their portrait does not need The Pragmatist. They need The Mirror.

The Longitudinal Agent runs on return visits and diffs new answers against session history: which unlived paths have moved, which fears have changed, which faculty responses the person engaged with. It generates a "what has changed in you" paragraph and updates the life graph, moving nodes from "unlived" to "in progress" when evidence supports it. This is what turns Faculty from a one-time experience into a relationship.

**Shared state schema:**

```python
SessionState = {
  "session_id": str,
  "user_profile": { "name": str, "github": str, "scraped_context": str },
  "observer_state": {
    "running_themes": [],
    "emotional_arc": [],
    "archetype_signals": { "quiet_fire": 0, "reluctant_pioneer": 0 },
    "answers_so_far": []
  },
  "archetype": str,
  "portrait": {},
  "graph": {},
  "faculty_responses": {},
  "counselor_brief": {},
  "history": []
}
```

No agent calls another agent directly. All communication happens through this shared object.

---

## Architecture Overview

```
Browser (index.html)
    |
    | Interview answers + scrape context
    v
Flask Server (server.py)
    |
    |-- /api/claude ---------> Anthropic API --> Claude Sonnet 4
    |                          (extract, match, portrait, graph, brief)
    |
    |-- /api/faculty --------> Anthropic API --> Claude Sonnet 4
    |                          (6 specialist voice responses, cached per node)
    |
    |-- /api/rag/query ------> Milvus Vector Store
    |                          (indexed research PDFs + counselor guidelines)
    |
    |-- /api/session/* ------> Local JSON files (sessions/)
    |
    |-- /api/scrape ---------> GitHub API + URL fetch
    |
    |-- /api/websearch ------> DuckDuckGo (no key required)
```

---

## API Routes

| Route | Method | What It Does |
|---|---|---|
| `GET /` | | Serves `index.html` - the main questionnaire |
| `GET /chat` | | Serves `chat.html` - the RAG mentor chatbot |
| `GET /dev` | | Serves `dev.html` - the indexer and admin console |
| `POST /api/claude` | JSON | Proxies calls to the Anthropic Messages API |
| `POST /api/scrape` | JSON | Scrapes GitHub API and any provided URLs |
| `POST /api/websearch` | JSON | DuckDuckGo search. Returns top 5 results. No key needed. |
| `POST /api/faculty` | JSON | Faculty agent. Takes node + answers + session_id. Returns voice + response. Persists to session. |
| `POST /api/session/save` | JSON | Saves full session to `sessions/` directory |
| `GET /api/session/load/:id` | | Returns full session JSON |
| `GET /api/session/list` | | Returns list of all sessions (id, archetype, date) |
| `POST /api/rag/query` | JSON | Queries Milvus via RAG pipeline |
| `GET /api/rag/stats` | | Returns Milvus status, chunk count, index type |
| `POST /api/dev/index` | FormData | Indexes uploaded PDFs into Milvus |
| `POST /api/dev/clear` | JSON | Drops Milvus collection |
| `GET /api/dev/export` | | Exports collection to `.npz` file |

---

## Running Locally

**Requirements:** Python 3.9+, pip, and an Anthropic API key (`ANTHROPIC_API_KEY`)

```bash
# Install core dependencies
pip install flask requests

# Optional: for RAG features
pip install pymilvus sentence-transformers pypdf2

# Required: export ANTHROPIC_API_KEY in your shell (the server exits if it is unset)

# Run
python server.py
```

Open:
- `http://localhost:8501` - the interview and knowledge graph
- `http://localhost:8501/chat` - the continuing conversation
- `http://localhost:8501/dev` - the counselor and parent upload interface

Milvus is optional. The questionnaire and chat work without it. The RAG indexer module (`indexer.py`) is not included in this repo, so `/chat` RAG and `/dev` indexing degrade gracefully. RAG activates only after you index documents via `/dev`.

---

# How We Used Claude

We used two models throughout the build: **Claude Sonnet 4.5** for speed-sensitive tasks and iteration, and **Claude Opus 4.7** for the deep reasoning work that required genuine psychological nuance.

---

## Claude as Prompt Engineer

The prompts that power The Latent Map - the entity extraction schema, the archetype matching logic, the six faculty voice instructions - were themselves designed in conversation with Claude. We described the psychological outcome we wanted and iterated on the system prompts until the output felt like a real mentor rather than a generic assistant. Claude helped us identify where prompts were leaking tone across voices, and where the JSON schema was too rigid to capture the range of human answers.

## Claude as Architect

When we hit structural decisions - how to design the blackboard session state, how to sequence the 5-step pipeline without downstream failures, how to handle RAG fallback gracefully - we talked them through with Claude before writing any code. The multi-agent architecture documented in the README came directly out of those conversations.

## Claude as the Runtime Intelligence

In the live application, Claude Sonnet 4.5 handles the agentic pipeline: entity extraction, archetype matching, portrait personalization, graph generation, and counselor brief. Every faculty voice response - The Socratic, The Pragmatist, The Mirror and the rest - is a Claude Sonnet call with a distinct system prompt. The RAG chatbot falls back to Claude when Milvus is unavailable.

## Claude as Debugging Partner

When the D3 graph broke, when JSON responses came back malformed, when a faculty voice started sounding like another - we debugged with Claude. It caught a schema mismatch in the graph generation step that would have taken us an hour to find manually.

In short: Claude was the co-builder, not just the API.

---

## The Bigger Picture

The question Faculty is trying to answer is not *"what personality type are you?"*

It is: **"What would you be doing if you had been seen clearly, earlier?"**

That question has a different answer for every person. And it has never had a scalable way to be asked - until now.

The person who uses Faculty at 18, again at 22, again at 28 - that person has something no previous generation had: a record of who they were trying to become, what got in the way, and evidence of whether they closed the gap.

That is not a product feature. That is a new kind of relationship with yourself.

---

## Links

- GitHub Repo: https://github.com/haiyashah/CMU-Claude-Hackathon/blob/main/README.md
- Devpost: https://devpost.com/software/the-latent-map
- Claude API Usage Documentation (Google Doc): https://docs.google.com/document/d/14vUC9fUhGSzphqnDjb2fKqh5FeWPryl-AtLFksHCS3Q/edit?tab=t.0#heading=h.wr4mkrbe8g3e
