import chroma_utils
from langchain_openai import ChatOpenAI
from llm_cache import get_cached, set_cached

MODEL = "gpt-4o-mini"

SYSTEM = """You are a code assistant. Answer questions using the provided code context.
Cite specific files in your answer. Be concise and technical."""

PROMPT_TMPL = """Context from repository:
{context}

Question: {question}"""


def answer_question(session_id: str, question: str) -> str:
    chunks = chroma_utils.search(session_id, question, n=5)
    if not chunks:
        return "Repository not yet indexed. Run analysis first."

    context_parts = []
    for c in chunks:
        fname = c["metadata"].get("file", "unknown")
        context_parts.append(f"# {fname}\n{c['text']}")
    context = "\n\n".join(context_parts)

    prompt = PROMPT_TMPL.format(context=context, question=question)
    cached = get_cached(MODEL, prompt)
    if cached:
        return cached

    llm = ChatOpenAI(model=MODEL, temperature=0)
    resp = llm.invoke([
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": prompt},
    ])
    answer = resp.content.strip()
    set_cached(MODEL, prompt, answer)
    return answer
