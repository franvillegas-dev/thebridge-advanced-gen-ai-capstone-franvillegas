from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


SUPERVISOR_PROMPT = load_prompt("supervisor")
TASKS_AGENT_PROMPT = load_prompt("tasks_agent")
CALENDAR_AGENT_PROMPT = load_prompt("calendar_agent")
CHAT_PROMPT = load_prompt("chat")
