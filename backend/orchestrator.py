from langgraph.graph import StateGraph, END
from state import RepoState
from agents.scanner import run_scanner
from agents.architecture import run_architecture
from agents.api_doc import run_api_doc
from agents.security import run_security
from agents.rag_setup import run_rag_setup


def build_graph():
    g = StateGraph(RepoState)

    g.add_node("scanner", run_scanner)
    g.add_node("architecture", run_architecture)
    g.add_node("api_doc", run_api_doc)
    g.add_node("security", run_security)
    g.add_node("rag_setup", run_rag_setup)

    g.set_entry_point("scanner")

    # Fan out to 4 parallel agents after scanner
    g.add_edge("scanner", "architecture")
    g.add_edge("scanner", "api_doc")
    g.add_edge("scanner", "security")
    g.add_edge("scanner", "rag_setup")

    g.add_edge("architecture", END)
    g.add_edge("api_doc", END)
    g.add_edge("security", END)
    g.add_edge("rag_setup", END)

    return g.compile()


def build_crisis_graph():
    from agents.crisis.ceo import ceo_response
    from agents.crisis.legal import legal_response
    from agents.crisis.engineer import engineer_response

    def crisis_ceo(state: dict) -> dict:
        finding = state.get("crisis_finding") or {}
        msg = ceo_response(finding)
        return {"crisis_messages": [msg]}

    def crisis_legal(state: dict) -> dict:
        finding = state.get("crisis_finding") or {}
        messages = state.get("crisis_messages", [])
        ceo_msg = next((m["content"] for m in messages if m["role"] == "CEO"), "")
        msg = legal_response(finding, ceo_msg)
        return {"crisis_messages": [msg]}

    def crisis_engineer(state: dict) -> dict:
        finding = state.get("crisis_finding") or {}
        messages = state.get("crisis_messages", [])
        legal_msg = next((m["content"] for m in messages if m["role"] == "Legal"), "")
        msg = engineer_response(finding, legal_msg)
        return {"crisis_messages": [msg]}

    g = StateGraph(RepoState)
    g.add_node("ceo", crisis_ceo)
    g.add_node("legal", crisis_legal)
    g.add_node("engineer", crisis_engineer)

    g.set_entry_point("ceo")
    g.add_edge("ceo", "legal")
    g.add_edge("legal", "engineer")
    g.add_edge("engineer", END)

    return g.compile()
