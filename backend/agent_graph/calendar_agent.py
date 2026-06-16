import logging
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from ..tools.calendar_tools import calendar_tools
from .state import AgentState

logger = logging.getLogger("agile_agent.calendar_agent")

CALENDAR_AGENT_PROMPT = """You are a calendar specialist. You help users:
- View upcoming deadlines and milestones
- Get sprint timelines
- Add calendar events for tracking"""


def create_calendar_agent():
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    logger.debug("Calendar agent created with tools: %s", [t.name for t in calendar_tools])
    return llm.bind_tools(calendar_tools)


def handle_calendar(state: AgentState) -> AgentState:
    from langchain_core.messages import AIMessage
    messages = state["messages"]
    logger.info("Calendar agent invoked — messages in history: %d", len(messages))
    try:
        agent = create_calendar_agent()
        system_msg = SystemMessage(content=CALENDAR_AGENT_PROMPT)
        response = agent.invoke([system_msg] + messages)
        logger.info("Calendar agent response received — content: %s", response.content[:200])
        return {**state, "messages": state["messages"] + [response]}
    except Exception as e:
        logger.error("Calendar agent error: %s", e)
        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content="Lo siento, no pude conectar con el asistente de IA. Verifica que GOOGLE_API_KEY esté configurada correctamente en backend/.env")
            ],
        }
