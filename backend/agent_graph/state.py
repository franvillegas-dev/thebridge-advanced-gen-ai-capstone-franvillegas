from typing import TypedDict, List, Optional, Any
from langchain_core.messages import AnyMessage


class AgentState(TypedDict):
    messages: List[AnyMessage]
    current_agent: Optional[str]
    pending_publish: List[dict[str, Any]]
    context: dict[str, Any]
