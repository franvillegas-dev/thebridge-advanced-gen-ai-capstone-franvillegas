import logging
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from .state import AgentState
from .supervisor import route_to_agent
from .jira_agent import handle_jira
from .tasks_agent import handle_tasks
from .calendar_agent import handle_calendar
from .story_agent import handle_story
from .llm import create_llm, invoke_with_retry, get_fallback_model_name, is_rate_limited

logger = logging.getLogger("agile_agent.graph")

CHAT_PROMPT = """You are a helpful AI assistant for an Agile project management system.
Answer the user's question conversationally. Be concise and friendly."""


def handle_chat(state: AgentState) -> AgentState:
    logger.info("Chat handler invoked")
    messages = state["messages"]
    try:
        llm = create_llm(temperature=0.7)
        system_msg = SystemMessage(content=CHAT_PROMPT)
        response = invoke_with_retry(llm, [system_msg] + messages)
        logger.info("Chat handler response received")
        return {**state, "messages": state["messages"] + [response]}
    except Exception as e:
        logger.error("Chat handler error: %s", e)
        if is_rate_limited(e):
            fallback_model = get_fallback_model_name()
            if fallback_model:
                try:
                    llm = create_llm(model=fallback_model, temperature=0.7)
                    system_msg = SystemMessage(content=CHAT_PROMPT)
                    response = invoke_with_retry(llm, [system_msg] + messages)
                    logger.info("Chat handler response via fallback %s", fallback_model)
                    return {**state, "messages": state["messages"] + [response]}
                except Exception as e2:
                    logger.error("Fallback chat handler also failed: %s", e2)
        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content=f"Lo siento, ocurrió un error: {e}")
            ],
        }


def build_graph() -> StateGraph:
    logger.info("Building LangGraph workflow")
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", lambda state: state)
    workflow.add_node("jira_agent", handle_jira)
    workflow.add_node("tasks_agent", handle_tasks)
    workflow.add_node("calendar_agent", handle_calendar)
    workflow.add_node("story_agent", handle_story)
    workflow.add_node("responder", handle_chat)

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

    compiled = workflow.compile()
    logger.info("LangGraph workflow compiled successfully")
    return compiled


graph = build_graph()


def log_invocation(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1].content if state["messages"] else ""
    agent = state.get("current_agent", "unknown")
    logger.info("Graph invoked — user_message=%s, current_agent=%s", last_msg[:100], agent)
    return state
