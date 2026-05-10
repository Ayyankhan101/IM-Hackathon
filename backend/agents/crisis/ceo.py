from langchain_openai import ChatOpenAI
from llm_cache import get_cached, set_cached

MODEL = "gpt-4o-mini"

SYSTEM = """You are the CEO woken at 2am about a security breach.
React with urgency, business impact focus, and decisive tone. 2-3 sentences max."""

PROMPT_TMPL = """Security finding: {finding_title}
Details: {exploit_story}

Respond as CEO. What is your immediate reaction and first order?"""


def ceo_response(finding: dict) -> dict:
    prompt = PROMPT_TMPL.format(
        finding_title=finding.get("title", "Unknown"),
        exploit_story=finding.get("exploit_story", ""),
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

    return {"role": "CEO", "content": text}
