import json
import logging
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from .state import AgentState
from .supervisor import route_to_agent
from .jira_agent import handle_jira
from .tasks_agent import handle_tasks
from .calendar_agent import handle_calendar
from .story_agent import handle_story
from .llm import create_llm, invoke_with_retry, get_fallback_model_name, is_rate_limited
from ..tools.jira_tools import jira_tools
from ..tools.tasks_tools import tasks_tools
from ..tools.calendar_tools import calendar_tools
from ..tools.story_tools import story_tools
from .utils import extract_text

logger = logging.getLogger("agile_agent.graph")

CHAT_PROMPT = """You are a helpful AI assistant for an Agile project management system.
Answer the user's question conversationally. Be concise and friendly."""

all_tools = jira_tools + tasks_tools + calendar_tools + story_tools
tool_node = ToolNode(all_tools)


def _last_message_summary(messages):
    if not messages:
        return "(empty)"
    last = messages[-1]
    content = getattr(last, "content", "")
    if isinstance(content, str):
        return content[:200]
    return str(content)[:200]


def handle_chat(state: AgentState) -> AgentState:
    current_agent = state.get("current_agent", "chat")
    logger.info(
        "Chat handler invoked — current_agent=%s, message_history=%d, last_message=%s",
        current_agent,
        len(state["messages"]),
        _last_message_summary(state["messages"]),
    )
    messages = state["messages"]
    try:
        llm = create_llm(temperature=0.7)
        system_msg = SystemMessage(content=CHAT_PROMPT)
        response = invoke_with_retry(llm, [system_msg] + messages)
        logger.info(
            "Chat handler response received — current_agent=%s, content_length=%d",
            current_agent,
            len(extract_text(response.content)),
        )
        logger.debug("Chat handler response content: %s", extract_text(response.content)[:500])
        return {**state, "messages": state["messages"] + [response]}
    except Exception as e:
        logger.error("Chat handler error: %s", e, extra={"agent": current_agent})
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


def should_continue(state: AgentState) -> str:
    messages = state["messages"]
    last_message = messages[-1]
    tool_calls = getattr(last_message, "tool_calls", None)
    if tool_calls:
        logger.info(
            "Agent requested tools — current_agent=%s, tool_calls=%s",
            state.get("current_agent", "unknown"),
            json.dumps(tool_calls, ensure_ascii=False)[:500],
        )
        return "tools"
    logger.info(
        "Agent finished — current_agent=%s, ending branch",
        state.get("current_agent", "unknown"),
    )
    return END


def log_invocation(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1].content if state["messages"] else ""
    session_id = state.get("context", {}).get("session_id", "")
    logger.info(
        "Graph invocation started — session_id=%s, message_count=%d, last_message=%s",
        session_id or "n/a",
        len(state["messages"]),
        last_msg[:200] if isinstance(last_msg, str) else str(last_msg)[:200],
    )
    logger.debug(
        "Full invocation state — session_id=%s, current_agent=%s",
        session_id or "n/a",
        state.get("current_agent", "none"),
    )
    return state


def logged_tool_node(state: AgentState) -> AgentState:
    """Run the tool node and log inputs/outputs for each tool call."""
    current_agent = state.get("current_agent", "unknown")
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", [])
    logger.info(
        "Tool node invoked — current_agent=%s, tool_calls_count=%d",
        current_agent,
        len(tool_calls),
    )
    for tc in tool_calls:
        logger.info(
            "Tool call — current_agent=%s, tool=%s, call_id=%s, args=%s",
            current_agent,
            tc.get("name", "unknown"),
            tc.get("id", "unknown"),
            json.dumps(tc.get("args", {}), ensure_ascii=False)[:500],
        )

    result = tool_node.invoke(state)

    tool_messages = result.get("messages", [])
    for tm in tool_messages:
        if getattr(tm, "type", None) == "tool":
            logger.info(
                "Tool result — tool=%s, call_id=%s, content_length=%d",
                getattr(tm, "name", "unknown"),
                getattr(tm, "tool_call_id", "unknown"),
                len(getattr(tm, "content", "")),
            )
            logger.debug("Tool result content: %s", str(getattr(tm, "content", ""))[:500])

    return result


def build_graph() -> StateGraph:
    logger.info("Building LangGraph workflow")
    workflow = StateGraph(AgentState)

    workflow.add_node("log_start", log_invocation)
    workflow.add_node("supervisor", lambda state: state)
    workflow.add_node("jira_agent", handle_jira)
    workflow.add_node("tasks_agent", handle_tasks)
    workflow.add_node("calendar_agent", handle_calendar)
    workflow.add_node("story_agent", handle_story)
    workflow.add_node("responder", handle_chat)
    workflow.add_node("tools", logged_tool_node)

    workflow.set_entry_point("log_start")
    workflow.add_edge("log_start", "supervisor")
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

    for agent in ["jira_agent", "tasks_agent", "calendar_agent", "story_agent"]:
        workflow.add_conditional_edges(
            agent,
            should_continue,
            {"tools": "tools", END: END},
        )

    workflow.add_conditional_edges(
        "tools",
        lambda state: state.get("current_agent", "responder"),
        {
            "jira_agent": "jira_agent",
            "tasks_agent": "tasks_agent",
            "calendar_agent": "calendar_agent",
            "story_agent": "story_agent",
            "responder": "responder",
        },
    )

    workflow.add_edge("responder", END)

    compiled = workflow.compile()
    logger.info("LangGraph workflow compiled successfully")
    return compiled


graph = build_graph()
