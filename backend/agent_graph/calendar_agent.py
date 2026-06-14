from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from ..tools.calendar_tools import calendar_tools
from .state import AgentState

CALENDAR_AGENT_PROMPT = """You are a calendar specialist. You help users:
- View upcoming deadlines and milestones
- Get sprint timelines
- Add calendar events for tracking"""


def create_calendar_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm.bind_tools(calendar_tools)


def handle_calendar(state: AgentState) -> AgentState:
    messages = state["messages"]
    agent = create_calendar_agent()
    system_msg = SystemMessage(content=CALENDAR_AGENT_PROMPT)
    response = agent.invoke([system_msg] + messages)
    return {**state, "messages": state["messages"] + [response]}
