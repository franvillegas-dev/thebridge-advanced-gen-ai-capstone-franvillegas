from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from ..tools.tasks_tools import tasks_tools
from .state import AgentState

TASKS_AGENT_PROMPT = """You are a task management specialist. You help users:
- Create, list, update, delete local tasks
- View today's pending tasks
- Publish local tasks to Jira as issues

Local tasks are private to this system until published to Jira."""


def create_tasks_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm.bind_tools(tasks_tools)


def handle_tasks(state: AgentState) -> AgentState:
    messages = state["messages"]
    agent = create_tasks_agent()
    system_msg = SystemMessage(content=TASKS_AGENT_PROMPT)
    response = agent.invoke([system_msg] + messages)
    return {**state, "messages": state["messages"] + [response]}
