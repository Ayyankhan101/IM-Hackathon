from typing import List, Optional, TypedDict
from typing_extensions import Annotated
import operator

def add(a: list, b: list) -> list:
    return a + b


class RepoState(TypedDict):
    # Input
    repo_url: str
    session_id: str

    # Scanner output
    local_path: str
    file_tree: List[str]
    file_contents: dict  # path -> content str

    # Agent outputs
    architecture_diagram: str
    api_endpoints: List[dict]
    security_findings: List[dict]
    rag_ready: bool

    # Parallel-writer lists — must use Annotated[List, add]
    events: Annotated[List[dict], add]
    crisis_messages: Annotated[List[dict], add]
    public_signals: Annotated[List[str], add]

    # Crisis state
    crisis_active: bool
    crisis_finding: Optional[dict]
