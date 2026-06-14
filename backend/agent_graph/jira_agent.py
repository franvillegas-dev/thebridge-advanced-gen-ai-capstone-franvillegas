from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from ..tools.jira_tools import jira_tools
from .state import AgentState

JIRA_AGENT_PROMPT = """You are a Jira specialist agent. You help users:
- Search and retrieve Jira issues
- Create new issues
- Update existing issues
- Generate reports on sprints and projects

Use the available tools to interact with Jira. Always confirm before destructive actions."""


def create_jira_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm.bind_tools(jira_tools)


def handle_jira(state: AgentState) -> AgentState:
    messages = state["messages"]
    agent = create_jira_agent()
    system_msg = SystemMessage(content=JIRA_AGENT_PROMPT)
    response = agent.invoke([system_msg] + messages)
    return {**state, "messages": state["messages"] + [response]}
