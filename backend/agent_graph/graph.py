from langgraph.graph import StateGraph, END
from .state import AgentState
from .supervisor import route_to_agent
from .jira_agent import handle_jira
from .tasks_agent import handle_tasks
from .calendar_agent import handle_calendar
from .story_agent import handle_story


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", lambda state: state)
    workflow.add_node("jira_agent", handle_jira)
    workflow.add_node("tasks_agent", handle_tasks)
    workflow.add_node("calendar_agent", handle_calendar)
    workflow.add_node("story_agent", handle_story)
    workflow.add_node("responder", lambda state: state)

    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "jira_agent": "jira_agent",
            "tasks_agent": "tasks_agent",
            "calendar_agent": "calendar_agent",
            "story_agent": "story_agent",
            "chat": "responder",
        },
    )
    workflow.add_edge("jira_agent", "responder")
    workflow.add_edge("tasks_agent", "responder")
    workflow.add_edge("calendar_agent", "responder")
    workflow.add_edge("story_agent", "responder")
    workflow.add_edge("responder", END)

    return workflow.compile()


graph = build_graph()
