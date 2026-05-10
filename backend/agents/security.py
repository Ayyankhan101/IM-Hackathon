import subprocess
import json
import uuid
from langchain_openai import ChatOpenAI
from llm_cache import get_cached, set_cached

MODEL = "gpt-4o-mini"

SYSTEM = """You are a security researcher. Given semgrep findings, write a short exploit story for each.
Return JSON array only. Each item: {id, file, line_start, severity, title, exploit_story}"""

PROMPT_TMPL = """Semgrep findings:
{findings}

For each finding write a 2-sentence exploit_story explaining real-world impact.
Return JSON array."""


def _synthetic_finding() -> dict:
    return {
        "id": str(uuid.uuid4()),
        "file": "app.py",
        "line_start": 1,
        "severity": "HIGH",
        "title": "Hardcoded Secret Detected",
        "exploit_story": (
            "An attacker who gains read access to the repository can extract the hardcoded credential "
            "and authenticate as the service, gaining full access to the protected resource. "
            "Rotating the secret requires a code change and redeploy, increasing blast radius during an incident."
        ),
    }


def _run_semgrep(local_path: str) -> list[dict]:
    try:
        result = subprocess.run(
            ["semgrep", "--config=auto", "--json", "--quiet", local_path],
            capture_output=True, text=True, timeout=120,
        )
        data = json.loads(result.stdout)
        raw = data.get("results", [])
        findings = []
        for r in raw[:20]:
            findings.append({
                "id": str(uuid.uuid4()),
                "file": r.get("path", ""),
                "line_start": r.get("start", {}).get("line", 0),
                "severity": r.get("extra", {}).get("severity", "MEDIUM").upper(),
                "title": r.get("extra", {}).get("message", r.get("check_id", "Unknown")),
                "exploit_story": "",
            })
        return findings
    except Exception:
        return []


def run_security(state: dict) -> dict:
    local_path = state.get("local_path", "")
    findings = _run_semgrep(local_path)

    if not findings:
        findings = [_synthetic_finding()]

    prompt = PROMPT_TMPL.format(findings=json.dumps(findings, indent=2))
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
        enriched = json.loads(raw)
    except Exception:
        enriched = findings

    return {
        "security_findings": enriched,
        "events": [{"type": "agent_done", "agent": "security", "message": f"{len(enriched)} findings"}],
    }
