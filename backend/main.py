import asyncio
import json
import os
import sys
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(__file__))

from orchestrator import build_graph, build_crisis_graph
from agents.chat import answer_question
from agents.crisis.reporter import reporter_alert

app = FastAPI(title="GitMind API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# session_id -> final RepoState
_sessions: dict = {}

analysis_graph = build_graph()
crisis_graph = build_crisis_graph()


# ── WebSocket: analysis ────────────────────────────────────────────────────────

@app.websocket("/ws/analyze")
async def ws_analyze(ws: WebSocket):
    await ws.accept()
    try:
        payload = await ws.receive_json()
        repo_url = payload.get("repo_url", "")
        session_id = payload.get("session_id", "default")

        if not repo_url:
            await ws.send_json({"type": "error", "message": "repo_url required"})
            return

        await ws.send_json({"type": "status", "message": "Starting analysis…"})

        initial_state = {
            "repo_url": repo_url,
            "session_id": session_id,
            "local_path": "",
            "file_tree": [],
            "file_contents": {},
            "architecture_diagram": "",
            "api_endpoints": [],
            "security_findings": [],
            "rag_ready": False,
            "events": [],
            "crisis_messages": [],
            "public_signals": [],
            "crisis_active": False,
            "crisis_finding": None,
        }

        loop = asyncio.get_event_loop()
        final_state = await loop.run_in_executor(
            None, lambda: analysis_graph.invoke(initial_state)
        )

        _sessions[session_id] = final_state

        # Stream events back
        for event in final_state.get("events", []):
            await ws.send_json({"type": "event", **event})

        await ws.send_json({
            "type": "result",
            "architecture_diagram": final_state.get("architecture_diagram", ""),
            "api_endpoints": final_state.get("api_endpoints", []),
            "security_findings": final_state.get("security_findings", []),
            "rag_ready": final_state.get("rag_ready", False),
        })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# ── HTTP: chat ─────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    question: str


@app.post("/chat")
async def chat(req: ChatRequest):
    loop = asyncio.get_event_loop()
    answer = await loop.run_in_executor(
        None, lambda: answer_question(req.session_id, req.question)
    )
    return {"answer": answer}


# ── HTTP: crisis ───────────────────────────────────────────────────────────────

class CrisisRequest(BaseModel):
    session_id: str
    finding_id: Optional[str] = None


@app.post("/crisis/start")
async def crisis_start(req: CrisisRequest):
    session = _sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found. Run analysis first.")

    findings = session.get("security_findings", [])
    if not findings:
        raise HTTPException(400, "No security findings to simulate crisis.")

    # Pick highest severity finding, or by id
    finding = findings[0]
    if req.finding_id:
        for f in findings:
            if f.get("id") == req.finding_id:
                finding = f
                break

    crisis_initial = {
        **session,
        "crisis_active": True,
        "crisis_finding": finding,
        "crisis_messages": [],
    }

    loop = asyncio.get_event_loop()
    crisis_state = await loop.run_in_executor(
        None, lambda: crisis_graph.invoke(crisis_initial)
    )

    # Reporter fires after crisis agents
    reporter_msg = reporter_alert(finding)
    messages = crisis_state.get("crisis_messages", []) + [reporter_msg]

    return {
        "finding": finding,
        "messages": messages,
    }


# ── HTTP: health ───────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}
