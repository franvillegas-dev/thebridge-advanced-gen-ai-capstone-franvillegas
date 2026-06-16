import logging
from typing import TypedDict, List, Optional, Any, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

logger = logging.getLogger("agile_agent.state")


class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    current_agent: Optional[str]
    pending_publish: List[dict[str, Any]]
    context: dict[str, Any]
