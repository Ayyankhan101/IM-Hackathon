# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: GitMind — Crisis Room

A repo intelligence multi-agent system. Paste a GitHub URL → 4 agents run in parallel → architecture diagram, API docs, security findings, and chat-with-repo Q&A. Optional stretch: Crisis Mode simulates a 2 a.m. security leak with CEO/Legal/Engineering/Reporter role-play agents.

**Golden rule:** A working demo with 4 features beats a broken demo with 10. Crisis Mode is a stretch goal — earn it by getting Analysis Mode solid first.

## Setup & Run

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install "fastapi[standard]" langgraph langchain langchain-openai chromadb gitpython tiktoken python-dotenv diskcache websockets semgrep
# Create backend/.env with: OPENAI_API_KEY=sk-...
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start          # dev server on :3000
```

### Test ChromaDB (must pass before anything else)
```python
import chromadb
client = chromadb.Client()
col = client.create_collection("test")
col.add(documents=["hello world"], ids=["1"])
print(col.query(query_texts=["hello"], n_results=1))  # must print 'hello world'
```

## Architecture

Two LangGraph graphs share a single typed state (`backend/state.py`):

- **Analysis Graph** (`orchestrator.py`): Scanner → parallel fan-out to Architect + API Documenter + Security Auditor + RAG Setup → END. Deterministic, runs once per repo.
- **Crisis Graph** (`agents/crisis/`): Sequential, event-driven. Triggered on demand from a high/critical security finding. CEO → Legal → Engineering agents take turns; Reporter fires on its own 45s timer.

Frontend connects via native WebSocket to `ws://localhost:8000/ws/analyze`. No extra WebSocket library needed.

## Project Structure

```
gitmind/
├── backend/
│   ├── main.py            # FastAPI app + WebSocket /ws/analyze + /chat HTTP endpoint
│   ├── state.py           # RepoState TypedDict — READ THIS FIRST (see critical note below)
│   ├── orchestrator.py    # LangGraph graph definition (build_graph())
│   ├── chroma_utils.py    # ChromaDB embed + search helpers
│   ├── llm_cache.py       # diskcache wrapper — never re-pay for same LLM call
│   └── agents/
│       ├── scanner.py     # git shallow-clone + file inventory (50MB / 300 file cap)
│       ├── architecture.py# file tree → Mermaid diagram (single LLM call, strict output)
│       ├── api_doc.py     # regex pre-filter routes → JSON endpoint docs
│       ├── security.py    # semgrep --config=auto + LLM triage → exploit stories
│       ├── rag_setup.py   # embed all chunks into ChromaDB
│       ├── chat.py        # RAG Q&A (top-5 chunks, cite files, on-demand via /chat)
│       └── crisis/        # STRETCH — ceo.py, legal.py, engineer.py, reporter.py
└── frontend/src/
    ├── App.jsx            # WebSocket logic + tab routing + SESSION_ID (uuidv4)
    ├── api.js             # WebSocket + HTTP helpers
    └── components/
        ├── AgentProgress.jsx  # live agent status panel (left sidebar)
        ├── DiagramTab.jsx     # Mermaid render with graceful parse-error fallback
        ├── DocsTab.jsx        # API endpoints with color-coded HTTP method badges
        ├── SecurityTab.jsx    # severity-colored finding cards + "Simulate Crisis" button
        ├── ChatTab.jsx        # RAG chat with bounce-dot loading indicator
        └── CrisisChat.jsx     # STRETCH — crisis transcript + Reporter timer
```

## Critical: State Schema (`backend/state.py`)

Any list that **multiple parallel agents write** must use `Annotated[List[X], add]` — this tells LangGraph to **merge** concurrent updates instead of last-writer-wins overwrite. Without it, parallel agents silently drop each other's events.

```python
# CORRECT — parallel agents all write to these:
events:           Annotated[List[dict], add]
security_findings: List[dict]   # only Security Auditor writes this
crisis_messages:  Annotated[List[dict], add]
public_signals:   Annotated[List[str], add]

# WRONG for parallel writers — plain List[X] causes silent data loss
```

Single-writer fields (e.g. `architecture_diagram` written only by Architect) do **not** need `Annotated`.

## LLM Usage

- Model: **`gpt-4o-mini`** only. Do NOT switch to gpt-4o — 10× cheaper, 3× faster, judges see results in 20s vs 60s.
- Always check `llm_cache.py` before calling the LLM: `get_cached(model, prompt)` / `set_cached(model, prompt, response)`.
- Cache key: `sha256(f"{model}::{prompt}")`, TTL 86400s.

## Mermaid Diagram Rules (Architect agent)

The frontend parser is strict. Violations break rendering silently:
- First line must be exactly: `graph TD`
- Node labels: only letters, numbers, spaces inside `[]` — NO parentheses, NO quotes
- Max 15 nodes
- Arrow labels: `-->|short label|`

## Security Agent

`semgrep --config=auto --json --quiet <local_path>` — fallback to `_synthetic_finding()` if semgrep fails so Crisis Mode always has something to demo.

Each finding shape: `{id, file, line_start, severity, title, exploit_story}`

## What Is Cut (do not add back)

- PostgreSQL or any real database — ChromaDB + in-memory dict is enough
- Docker — run locally for the demo
- User accounts / login
- License checker, multi-repo comparison
- tree-sitter AST parsing
- 10-agent crisis room — trimmed to 3 crisis agents + Reporter timer
