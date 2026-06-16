import logging
from langchain_core.prompts import ChatPromptTemplate
from .llm import create_llm, invoke_with_retry, get_fallback_model_name, is_rate_limited
from .state import AgentState

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
    logger.info("Routing message: %s", last_message[:120])
    try:
        response = invoke_with_retry(_supervisor_chain, {"input": last_message})
        agent_name = response.content.strip().lower()
        logger.info("Supervisor routed to: %s", agent_name)
    except Exception as e:
        logger.error("Supervisor error: %s — falling back to chat", e)
        if is_rate_limited(e):
            fallback_model = get_fallback_model_name()
            if fallback_model:
                try:
                    fallback_llm = create_llm(model=fallback_model, temperature=0)
                    fallback_chain = _prompt | fallback_llm
                    response = invoke_with_retry(fallback_chain, {"input": last_message})
                    agent_name = response.content.strip().lower()
                    logger.info("Supervisor routed via fallback %s to: %s", fallback_model, agent_name)
                    if agent_name in {"jira_agent", "tasks_agent", "calendar_agent", "story_agent", "chat"}:
                        return agent_name
                except Exception as e2:
                    logger.error("Fallback supervisor also failed: %s", e2)
        return "chat"
    valid_agents = {"jira_agent", "tasks_agent", "calendar_agent", "story_agent", "chat"}
    if agent_name not in valid_agents:
        logger.warning("Supervisor returned invalid agent: %s — falling back to chat", agent_name)
        return "chat"
    return agent_name
