from langchain_openai import ChatOpenAI
from llm_cache import get_cached, set_cached

MODEL = "gpt-4o-mini"

SYSTEM = """You are the on-call engineering lead responding to a 2am security incident.
Focus on technical remediation steps, immediate mitigations, and RCA. 2-3 sentences max."""

PROMPT_TMPL = """Security finding: {finding_title}
File: {file} line {line}
Details: {exploit_story}
Legal concern: {legal_message}

Respond as Engineering Lead. What is your immediate technical fix and containment plan?"""


def engineer_response(finding: dict, legal_message: str) -> dict:
    prompt = PROMPT_TMPL.format(
        finding_title=finding.get("title", "Unknown"),
        file=finding.get("file", "unknown"),
        line=finding.get("line_start", 0),
        exploit_story=finding.get("exploit_story", ""),
        legal_message=legal_message,
    )
    cached = get_cached(MODEL, prompt)
    if cached:
        text = cached
    else:
        llm = ChatOpenAI(model=MODEL, temperature=0.7)
        resp = llm.invoke([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ])
        text = resp.content.strip()
        set_cached(MODEL, prompt, text)

    return {"role": "Engineering", "content": text}
