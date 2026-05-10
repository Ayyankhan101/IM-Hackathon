import chromadb
from chromadb.utils import embedding_functions

_client = chromadb.Client()
_ef = embedding_functions.DefaultEmbeddingFunction()

_collections: dict = {}


def get_collection(session_id: str):
    name = f"repo_{session_id.replace('-', '_')}"
    if name not in _collections:
        _collections[name] = _client.get_or_create_collection(
            name=name,
            embedding_function=_ef,
        )
    return _collections[name]


def embed_chunks(session_id: str, chunks: list[dict]):
    """chunks: list of {id, text, metadata}"""
    col = get_collection(session_id)
    col.add(
        documents=[c["text"] for c in chunks],
        ids=[c["id"] for c in chunks],
        metadatas=[c.get("metadata", {}) for c in chunks],
    )


def search(session_id: str, query: str, n: int = 5) -> list[dict]:
    col = get_collection(session_id)
    count = col.count()
    if count == 0:
        return []
    results = col.query(query_texts=[query], n_results=min(n, count))
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    return [{"text": d, "metadata": m} for d, m in zip(docs, metas)]
