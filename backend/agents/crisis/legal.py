from langchain_openai import ChatOpenAI
from llm_cache import get_cached, set_cached

MODEL = "gpt-4o-mini"

SYSTEM = """You are General Counsel responding to a 2am security incident call.
Focus on regulatory exposure, disclosure obligations, and liability mitigation. 2-3 sentences max."""

PROMPT_TMPL = """Security finding: {finding_title}
CEO said: {ceo_message}
Details: {exploit_story}

Respond as General Counsel. What legal actions must happen immediately?"""


def legal_response(finding: dict, ceo_message: str) -> dict:
    prompt = PROMPT_TMPL.format(
        finding_title=finding.get("title", "Unknown"),
        ceo_message=ceo_message,
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

    return {"role": "Legal", "content": text}
