import logging
from langchain_core.messages import SystemMessage
from .llm import create_llm, invoke_with_retry, get_fallback_model_name, is_rate_limited
from ..tools.jira_tools import jira_tools
from .state import AgentState
from .utils import extract_text

logger = logging.getLogger("agile_agent.jira_agent")

JIRA_AGENT_PROMPT = """You are a Jira specialist agent. You help users:
- Search and retrieve Jira issues
- Create new issues
- Update existing issues
- Generate reports on sprints and projects

Use the available tools to interact with Jira. Always confirm before destructive actions."""


def create_jira_agent():
    llm = create_llm(temperature=0)
    logger.debug("Jira agent created with tools: %s", [t.name for t in jira_tools])
    return llm.bind_tools(jira_tools)


def handle_jira(state: AgentState) -> AgentState:
    from langchain_core.messages import AIMessage
    messages = state["messages"]
    session_id = state.get("context", {}).get("session_id", "")
    last_message = messages[-1].content if messages else ""
    logger.info(
        "Jira agent invoked — session_id=%s, history=%d, last_message=%s",
        session_id or "n/a",
        len(messages),
        last_message[:200] if isinstance(last_message, str) else str(last_message)[:200],
    )
    try:
        agent = create_jira_agent()
        system_msg = SystemMessage(content=JIRA_AGENT_PROMPT)
        response = invoke_with_retry(agent, [system_msg] + messages)
        tool_calls = getattr(response, "tool_calls", None)
        logger.info(
            "Jira agent response — session_id=%s, content_length=%d, tool_calls=%s",
            session_id or "n/a",
            len(extract_text(response.content)),
            len(tool_calls) if tool_calls else 0,
        )
        logger.debug("Jira agent response content: %s", extract_text(response.content)[:500])
        return {**state, "current_agent": "jira_agent", "messages": state["messages"] + [response]}
    except Exception as e:
        logger.error("Jira agent error — session_id=%s, error=%s", session_id or "n/a", e)
        if is_rate_limited(e):
            fallback_model = get_fallback_model_name()
            if fallback_model:
                try:
                    fallback_llm = create_llm(model=fallback_model, temperature=0)
                    fallback_agent = fallback_llm.bind_tools(jira_tools)
                    response = invoke_with_retry(fallback_agent, [system_msg] + messages)
                    logger.info("Jira agent response via fallback %s", fallback_model)
                    return {**state, "current_agent": "jira_agent", "messages": state["messages"] + [response]}
                except Exception as e2:
                    logger.error("Fallback Jira agent also failed: %s", e2)
        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content="Lo siento, no pude conectar con el asistente de IA. Verifica que GOOGLE_API_KEY esté configurada correctamente en backend/.env o que la cuota de la API no esté agotada.")
            ],
        }
