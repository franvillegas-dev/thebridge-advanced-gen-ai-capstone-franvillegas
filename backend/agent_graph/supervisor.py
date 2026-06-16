from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import AgentState

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
_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
_supervisor_chain = _prompt | _llm


def route_to_agent(state: AgentState) -> str:
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    try:
        response = _supervisor_chain.invoke({"input": last_message})
        agent_name = response.content.strip().lower()
    except Exception:
        return "chat"
    valid_agents = {"jira_agent", "tasks_agent", "calendar_agent", "story_agent", "chat"}
    return agent_name if agent_name in valid_agents else "chat"
