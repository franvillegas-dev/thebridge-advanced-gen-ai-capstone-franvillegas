import logging
from langchain_core.messages import SystemMessage
from .llm import create_llm, invoke_with_retry, get_fallback_model_name, is_rate_limited
from ..tools.tasks_tools import tasks_tools
from .state import AgentState
from .utils import extract_text

logger = logging.getLogger("agile_agent.tasks_agent")

TASKS_AGENT_PROMPT = """You are a task management specialist. You help users:
- Create, list, update, delete local tasks
- View today's pending tasks
- Publish local tasks to Jira as issues

Local tasks are private to this system until published to Jira."""


def create_tasks_agent():
    llm = create_llm(temperature=0)
    logger.debug("Tasks agent created with tools: %s", [t.name for t in tasks_tools])
    return llm.bind_tools(tasks_tools)


def handle_tasks(state: AgentState) -> AgentState:
    from langchain_core.messages import AIMessage
    messages = state["messages"]
    session_id = state.get("context", {}).get("session_id", "")
    last_message = messages[-1].content if messages else ""
    logger.info(
        "Tasks agent invoked — session_id=%s, history=%d, last_message=%s",
        session_id or "n/a",
        len(messages),
        last_message[:200] if isinstance(last_message, str) else str(last_message)[:200],
    )
    try:
        agent = create_tasks_agent()
        system_msg = SystemMessage(content=TASKS_AGENT_PROMPT)
        response = invoke_with_retry(agent, [system_msg] + messages)
        tool_calls = getattr(response, "tool_calls", None)
        logger.info(
            "Tasks agent response — session_id=%s, content_length=%d, tool_calls=%s",
            session_id or "n/a",
            len(extract_text(response.content)),
            len(tool_calls) if tool_calls else 0,
        )
        logger.debug("Tasks agent response content: %s", extract_text(response.content)[:500])
        return {**state, "current_agent": "tasks_agent", "messages": state["messages"] + [response]}
    except Exception as e:
        logger.error("Tasks agent error — session_id=%s, error=%s", session_id or "n/a", e)
        if is_rate_limited(e):
            fallback_model = get_fallback_model_name()
            if fallback_model:
                try:
                    fallback_llm = create_llm(model=fallback_model, temperature=0)
                    fallback_agent = fallback_llm.bind_tools(tasks_tools)
                    response = invoke_with_retry(fallback_agent, [system_msg] + messages)
                    logger.info("Tasks agent response via fallback %s", fallback_model)
                    return {**state, "current_agent": "tasks_agent", "messages": state["messages"] + [response]}
                except Exception as e2:
                    logger.error("Fallback tasks agent also failed: %s", e2)
        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content="Lo siento, no pude conectar con el asistente de IA. Verifica que GOOGLE_API_KEY esté configurada correctamente en backend/.env o que la cuota de la API no esté agotada.")
            ],
        }
