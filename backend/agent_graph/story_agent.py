import logging
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from ..tools.story_tools import story_tools
from .state import AgentState

logger = logging.getLogger("agile_agent.story_agent")

STORY_AGENT_PROMPT = """You are a story refinement specialist. You help users:
- Refine raw feature descriptions into well-structured user stories
- Split large stories into smaller independent ones
- Estimate effort in story points"""


def create_story_agent():
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    logger.debug("Story agent created with tools: %s", [t.name for t in story_tools])
    return llm.bind_tools(story_tools)


def handle_story(state: AgentState) -> AgentState:
    from langchain_core.messages import AIMessage
    messages = state["messages"]
    logger.info("Story agent invoked — messages in history: %d", len(messages))
    try:
        agent = create_story_agent()
        system_msg = SystemMessage(content=STORY_AGENT_PROMPT)
        response = agent.invoke([system_msg] + messages)
        logger.info("Story agent response received — content: %s", response.content[:200])
        return {**state, "messages": state["messages"] + [response]}
    except Exception as e:
        logger.error("Story agent error: %s", e)
        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content="Lo siento, no pude conectar con el asistente de IA. Verifica que GOOGLE_API_KEY esté configurada correctamente en backend/.env")
            ],
        }
