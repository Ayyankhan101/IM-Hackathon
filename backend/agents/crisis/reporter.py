from langchain_openai import ChatOpenAI
from llm_cache import get_cached, set_cached

MODEL = "gpt-4o-mini"

SYSTEM = """You are an investigative tech journalist who has just received a tip about a security breach.
Write a breaking news tweet / short press alert. Dramatic but factual. Max 2 sentences."""

PROMPT_TMPL = """Security breach at a software company. Finding: {finding_title}
Alleged impact: {exploit_story}

Write a breaking news alert as an investigative reporter."""


def reporter_alert(finding: dict) -> dict:
    prompt = PROMPT_TMPL.format(
        finding_title=finding.get("title", "Unknown"),
        exploit_story=finding.get("exploit_story", ""),
    )
    cached = get_cached(MODEL, prompt)
    if cached:
        text = cached
    else:
        llm = ChatOpenAI(model=MODEL, temperature=0.9)
        resp = llm.invoke([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ])
        text = resp.content.strip()
        set_cached(MODEL, prompt, text)

    return {"role": "Reporter", "content": text}
