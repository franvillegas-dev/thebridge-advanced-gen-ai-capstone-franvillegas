from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from .state import AgentState

SUPERVISOR_PROMPT = """You are a supervisor agent for a Jira project management system.
Route the user's message to the most appropriate specialist agent:

- jira_agent: For anything about Jira issues, sprints, reports, searching projects
- tasks_agent: For daily tasks, todo lists, task management, publishing to Jira
- calendar_agent: For deadlines, milestones, sprint timelines, dates
- story_agent: For refining user stories, splitting stories, estimating effort
- chat: For general conversation, greetings, help

Respond with ONLY the agent name: jira_agent, tasks_agent, calendar_agent, story_agent, or chat"""


def create_supervisor_chain():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return SUPERVISOR_PROMPT | llm


def route_to_agent(state: AgentState) -> str:
    messages = state["messages"]
    chain = create_supervisor_chain()
    response = chain.invoke({"messages": messages})
    agent_name = response.content.strip().lower()
    valid_agents = {"jira_agent", "tasks_agent", "calendar_agent", "story_agent", "chat"}
    return agent_name if agent_name in valid_agents else "chat"
