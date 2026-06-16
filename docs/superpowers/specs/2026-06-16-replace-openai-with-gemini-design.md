# Replace OpenAI with Google Gemini 2.0 Flash

## Overview

Replace OpenAI (`gpt-4o-mini` via `langchain-openai`) with Google Gemini 2.0 Flash (`langchain-google-genai`) across the entire project.

## Scope

### Backend Python files (6 files)

| File | Change |
|------|--------|
| `agent_graph/supervisor.py` | `ChatOpenAI` → `ChatGoogleGenerativeAI`, model: `gemini-2.0-flash` |
| `agent_graph/jira_agent.py` | Same + update error message |
| `agent_graph/story_agent.py` | Same + update error message |
| `agent_graph/tasks_agent.py` | Same + update error message |
| `agent_graph/calendar_agent.py` | Same + update error message |
| `tools/story_tools.py` | Same (3 instances with temperatures 0.3, 0.3, 0.2) |

### Configuration (2 files)

| File | Change |
|------|--------|
| `backend/pyproject.toml` | `langchain-openai` → `langchain-google-genai>=2.0.0` |
| `backend/.env.example` | `OPENAI_API_KEY` → `GOOGLE_API_KEY` |

### Documentation (4 files)

| File | Change |
|------|--------|
| `README.md` | OpenAI references → Google/GOOGLE_API_KEY |
| `docs/superpowers/specs/2026-06-16-dashboard-homepage-and-chat-panel-design.md` | Same |
| `docs/superpowers/plans/2026-06-16-dashboard-homepage-and-chat-panel.md` | Same |
| `docs/superpowers/plans/2026-06-14-jira-multi-agent-system-implementation.md` | Same |

### Not affected

- Frontend: no changes needed (it reads config endpoint generically)
- `.env` (real): not tracked in git; user renames the variable manually

## Migration details

```
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
```

Error messages change from "Verifica que OPENAI_API_KEY esté configurada" to "Verifica que GOOGLE_API_KEY esté configurada".

`temperature` parameter is fully supported by `ChatGoogleGenerativeAI`.
