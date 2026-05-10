import re
import json
from langchain_openai import ChatOpenAI
from llm_cache import get_cached, set_cached

MODEL = "gpt-4o-mini"

ROUTE_PATTERNS = [
    # FastAPI / Flask / Express
    re.compile(r'@(?:app|router)\.(get|post|put|patch|delete|head|options)\s*\(\s*["\']([^"\']+)["\']', re.I),
    # Express router
    re.compile(r'router\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']', re.I),
    # Django urls
    re.compile(r'path\s*\(\s*["\']([^"\']+)["\']', re.I),
]

SYSTEM = """You document REST API endpoints. Return a JSON array only, no markdown.
Each item: {"method": "GET", "path": "/foo", "description": "...", "params": [], "response": "..."}"""

PROMPT_TMPL = """These routes were found in the codebase:
{routes}

Relevant code snippets:
{snippets}

Return JSON array of endpoint objects."""


def _extract_routes(file_contents: dict) -> list[dict]:
    found = []
    for path, content in file_contents.items():
        for pat in ROUTE_PATTERNS:
            for m in pat.finditer(content):
                if len(m.groups()) == 2:
                    method, route = m.group(1).upper(), m.group(2)
                else:
                    method, route = "GET", m.group(1)
                found.append({"method": method, "path": route, "file": path})
    return found[:50]


def _snippets(routes: list[dict], file_contents: dict) -> str:
    seen = set()
    parts = []
    for r in routes[:10]:
        f = r["file"]
        if f in seen:
            continue
        seen.add(f)
        parts.append(f"# {f}\n{file_contents.get(f, '')[:800]}")
    return "\n\n".join(parts)


def run_api_doc(state: dict) -> dict:
    file_contents = state.get("file_contents", {})
    routes = _extract_routes(file_contents)

    if not routes:
        return {
            "api_endpoints": [],
            "events": [{"type": "agent_done", "agent": "api_doc", "message": "No routes found"}],
        }

    routes_str = json.dumps(routes, indent=2)
    snippets = _snippets(routes, file_contents)
    prompt = PROMPT_TMPL.format(routes=routes_str, snippets=snippets)

    cached = get_cached(MODEL, prompt)
    if cached:
        raw = cached
    else:
        llm = ChatOpenAI(model=MODEL, temperature=0)
        resp = llm.invoke([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ])
        raw = resp.content.strip()
        set_cached(MODEL, prompt, raw)

    try:
        endpoints = json.loads(raw)
    except Exception:
        endpoints = routes  # fallback to raw extracted routes

    return {
        "api_endpoints": endpoints,
        "events": [{"type": "agent_done", "agent": "api_doc", "message": f"{len(endpoints)} endpoints documented"}],
    }
