from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from ..tools.story_tools import story_tools
from .state import AgentState

STORY_AGENT_PROMPT = """You are a story refinement specialist. You help users:
- Refine raw feature descriptions into well-structured user stories
- Split large stories into smaller independent ones
- Estimate effort in story points"""


def create_story_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm.bind_tools(story_tools)


def handle_story(state: AgentState) -> AgentState:
    messages = state["messages"]
    agent = create_story_agent()
    system_msg = SystemMessage(content=STORY_AGENT_PROMPT)
    response = agent.invoke([system_msg] + messages)
    return {**state, "messages": state["messages"] + [response]}
