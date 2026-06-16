import logging
from langchain_core.prompts import ChatPromptTemplate
from .llm import create_llm, invoke_with_retry, get_fallback_model_name, is_rate_limited
from .state import AgentState
from .utils import extract_text

logger = logging.getLogger("agile_agent.supervisor")

SUPERVISOR_PROMPT = """You are a supervisor agent for a Jira project management system.
Route the user's message to the most appropriate specialist agent:

- jira_agent: For anything about Jira issues, sprints, reports, searching projects
- tasks_agent: For daily tasks, todo lists, task management, publishing to Jira
- calendar_agent: For deadlines, milestones, sprint timelines, dates
- story_agent: For refining user stories, splitting stories, estimating effort
- chat: For general conversation, greetings, help

Respond with ONLY the agent name: jira_agent, tasks_agent, calendar_agent, story_agent, or chat"""

_prompt = ChatPromptTemplate.from_messages([
    ("system", SUPERVISOR_PROMPT),
    ("human", "{input}"),
])
_llm = create_llm(temperature=0)
_supervisor_chain = _prompt | _llm


def route_to_agent(state: AgentState) -> str:
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    session_id = state.get("context", {}).get("session_id", "")
    logger.info(
        "Supervisor routing — session_id=%s, message_length=%d, message=%s",
        session_id or "n/a",
        len(last_message),
        last_message[:200],
    )
    try:
        response = invoke_with_retry(_supervisor_chain, {"input": last_message})
        raw_content = response.content
        agent_name = extract_text(raw_content).strip().lower()
        logger.info(
            "Supervisor decision — session_id=%s, selected_agent=%s",
            session_id or "n/a",
            agent_name,
        )
        logger.debug("Supervisor raw response: %s", raw_content)
    except Exception as e:
        logger.error(
            "Supervisor routing error — session_id=%s, error=%s",
            session_id or "n/a",
            e,
        )
        if is_rate_limited(e):
            fallback_model = get_fallback_model_name()
            if fallback_model:
                try:
                    fallback_llm = create_llm(model=fallback_model, temperature=0)
                    fallback_chain = _prompt | fallback_llm
                    response = invoke_with_retry(fallback_chain, {"input": last_message})
                    agent_name = extract_text(response.content).strip().lower()
                    logger.info(
                        "Supervisor decision via fallback — session_id=%s, fallback_model=%s, selected_agent=%s",
                        session_id or "n/a",
                        fallback_model,
                        agent_name,
                    )
                    if agent_name in {"jira_agent", "tasks_agent", "calendar_agent", "story_agent", "chat"}:
                        return agent_name
                except Exception as e2:
                    logger.error("Fallback supervisor also failed: %s", e2)
        logger.info("Supervisor fallback to chat due to error")
        return "chat"
    valid_agents = {"jira_agent", "tasks_agent", "calendar_agent", "story_agent", "chat"}
    if agent_name not in valid_agents:
        logger.warning(
            "Supervisor returned invalid agent — session_id=%s, raw_response=%s, falling_back=chat",
            session_id or "n/a",
            agent_name,
        )
        return "chat"
    return agent_name
