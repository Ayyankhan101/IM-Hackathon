import uuid
import chroma_utils

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def _chunk_text(text: str, path: str) -> list[dict]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        chunks.append({
            "id": str(uuid.uuid4()),
            "text": chunk,
            "metadata": {"file": path, "start": start},
        })
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def run_rag_setup(state: dict) -> dict:
    session_id = state["session_id"]
    file_contents = state.get("file_contents", {})

    all_chunks = []
    for path, content in file_contents.items():
        if not content.strip():
            continue
        all_chunks.extend(_chunk_text(content, path))

    if all_chunks:
        chroma_utils.embed_chunks(session_id, all_chunks)

    return {
        "rag_ready": True,
        "events": [{"type": "agent_done", "agent": "rag_setup", "message": f"Embedded {len(all_chunks)} chunks"}],
    }
