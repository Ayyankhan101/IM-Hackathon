from langchain_openai import ChatOpenAI
from llm_cache import get_cached, set_cached

MODEL = "gpt-4o-mini"

SYSTEM = """You output Mermaid diagrams only. Rules:
- First line exactly: graph TD
- Node labels: only letters numbers spaces inside []
- Max 15 nodes
- Arrow labels: -->|short label|
- No parentheses, no quotes in node labels
- No markdown fences, no explanation"""

PROMPT_TMPL = """File tree:
{tree}

Produce a Mermaid graph TD diagram showing architecture. Max 15 nodes."""


def run_architecture(state: dict) -> dict:
    tree_str = "\n".join(state["file_tree"][:200])
    prompt = PROMPT_TMPL.format(tree=tree_str)

    cached = get_cached(MODEL, prompt)
    if cached:
        diagram = cached
    else:
        llm = ChatOpenAI(model=MODEL, temperature=0)
        resp = llm.invoke([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ])
        diagram = resp.content.strip()
        set_cached(MODEL, prompt, diagram)

    # Ensure first line is correct
    lines = diagram.splitlines()
    if not lines or lines[0].strip() != "graph TD":
        diagram = "graph TD\n" + diagram

    return {
        "architecture_diagram": diagram,
        "events": [{"type": "agent_done", "agent": "architecture", "message": "Diagram ready"}],
    }
