import hashlib
import diskcache

_cache = diskcache.Cache("/tmp/gitmind_llm_cache", size_limit=500_000_000)
TTL = 86400


def _key(model: str, prompt: str) -> str:
    return hashlib.sha256(f"{model}::{prompt}".encode()).hexdigest()


def get_cached(model: str, prompt: str):
    return _cache.get(_key(model, prompt))


def set_cached(model: str, prompt: str, response: str):
    _cache.set(_key(model, prompt), response, expire=TTL)
