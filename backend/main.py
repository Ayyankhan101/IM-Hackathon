import logging
import os
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# load_dotenv MUST run before any LangChain / OpenAI import
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.chat import run_chat_agent
from orchestrator import graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-30s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── Startup validation ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set.\n"
            "Create backend/.env with:  OPENAI_API_KEY=sk-..."
        )
    logger.info("GitMind backend starting — OPENAI_API_KEY present")
    yield
    logger.info("GitMind backend shutting down")


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="GitMind API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store — keyed by session_id UUID
# Shape: {repo_name, chroma_collection_name, security_findings, chat_history}
sessions: dict[str, dict] = {}


# ── Request models ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    question:   str


# ── State initialiser (single source of truth for initial RepoState) ──────────

def _initial_state(repo_url: str) -> dict:
    return {
        "repo_url":               repo_url,
        "local_path":             None,
        "file_tree":              [],
        "file_contents":          {},
        "repo_name":              "",
        "architecture_diagram":   None,
        "api_docs":               [],
        "security_findings":      [],
        "chroma_collection_name": None,
        "chat_history":           [],
        "selected_finding_id":    None,
        "crisis_messages":        [],
        "crisis_turn":            0,
        "public_signals":         [],
        "reporter_published":     False,
        "crisis_resolved":        False,
        "events":                 [],
    }


# ── Agent → frontend status mapping ───────────────────────────────────────────

_STATUS_MAP: dict[str, dict[str, str]] = {
    "scanner":      {
        "scanner": "done", "architecture": "running",
        "api_docs": "running", "security": "running", "chat": "running",
    },
    "architecture": {"architecture": "done"},
    "api_docs":     {"api_docs": "done"},
    "security":     {"security": "done"},
    "rag_setup":    {"chat": "done"},
}


# ── WebSocket endpoint ─────────────────────────────────────────────────────────

@app.websocket("/ws/analyze")
async def ws_analyze(ws: WebSocket):
    await ws.accept()

    try:
        payload = await ws.receive_json()
    except Exception:
        await ws.close(code=1003)
        return

    repo_url   = (payload.get("repo_url") or "").strip()
    session_id = payload.get("session_id") or str(uuid.uuid4())

    if not repo_url:
        await ws.send_json({"error": "repo_url is required"})
        await ws.close()
        return

    logger.info("Analysis started  session=%s  repo=%s", session_id, repo_url)
    initial    = _initial_state(repo_url)
    final_state = dict(initial)

    await ws.send_json({"agent_status": {"scanner": "running"}})

    try:
        async for chunk in graph.astream(initial, stream_mode="updates"):
            for node, update in chunk.items():
                msg: dict = {"agent_status": _STATUS_MAP.get(node, {})}

                # Relay result payloads to the frontend as they arrive
                for key in (
                    "architecture_diagram",
                    "api_docs",
                    "security_findings",
                    "chroma_collection_name",
                ):
                    if key in update:
                        msg[key]           = update[key]
                        final_state[key]   = update[key]

                if "repo_name" in update:
                    final_state["repo_name"] = update["repo_name"]

                # Surface agent errors to the frontend without crashing the stream
                for ev in update.get("events", []):
                    if ev.get("status") == "error":
                        msg["agent_error"] = ev
                        logger.warning("Agent error surfaced: %s", ev)

                await ws.send_json(msg)

    except WebSocketDisconnect:
        logger.info("Client disconnected mid-analysis  session=%s", session_id)
        return
    except Exception as exc:
        logger.error("Analysis pipeline error  session=%s: %s", session_id, exc)
        await ws.send_json({"error": str(exc)})
        await ws.close()
        return

    sessions[session_id] = {
        "repo_name":              final_state["repo_name"],
        "chroma_collection_name": final_state["chroma_collection_name"],
        "security_findings":      final_state["security_findings"],
        "chat_history":           [],
    }

    await ws.send_json({"done": True, "session_id": session_id})
    logger.info("Analysis complete  session=%s  repo=%s", session_id, final_state["repo_name"])


# ── Chat endpoint ──────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    session = sessions.get(req.session_id)
    if not session:
        return {"error": "Session not found. Run /ws/analyze first."}

    if not session.get("chroma_collection_name"):
        return {"error": "Knowledge base not ready — RAG setup may have failed."}

    answer = run_chat_agent(
        question=req.question,
        collection_name=session["chroma_collection_name"],
        chat_history=session["chat_history"],
        repo_name=session["repo_name"],
    )

    session["chat_history"].extend([
        {"role": "user",      "content": req.question},
        {"role": "assistant", "content": answer},
    ])

    return {"answer": answer}


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "running", "sessions_active": len(sessions)}
