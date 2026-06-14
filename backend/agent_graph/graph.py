from langgraph.graph import StateGraph, END
from .state import AgentState
from .supervisor import route_to_agent


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", lambda state: state)
    workflow.add_node("responder", lambda state: state)

    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "jira_agent": "responder",
            "tasks_agent": "responder",
            "calendar_agent": "responder",
            "story_agent": "responder",
            "chat": "responder",
        },
    )
    workflow.add_edge("responder", END)

    return workflow.compile()


graph = build_graph()
