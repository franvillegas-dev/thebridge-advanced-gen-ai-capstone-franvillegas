# Interactive Agent Creation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the chat assistant confirm created tasks/events with rich cards, refresh the matching view without reloading, ask the user for missing info, and detect calendar overlaps.

**Architecture:** Extend the calendar schema with time ranges, move prompts to external English files, add structured SSE action events from the backend, and use TanStack Query on the frontend for selective view refresh.

**Tech Stack:** Next.js 16, React 19, TypeScript, TanStack Query, Drizzle ORM, Python 3.12, LangGraph, SQLite.

---

### File map

| File | Responsibility |
|------|----------------|
| `frontend/drizzle/schema.ts` | Add `startTime`/`endTime` to `calendarEvents`. |
| `frontend/drizzle/migrations/0001_add_event_times.sql` | Migration for new columns + defaults. |
| `backend/agent_graph/prompts/__init__.py` | Helper to load prompt files. |
| `backend/agent_graph/prompts/*.md` | External agent prompts in English. |
| `backend/agent_graph/state.py` | Add `pending_action` to state. |
| `backend/agent_graph/supervisor.py` | Route based on `pending_action`. |
| `backend/agent_graph/calendar_agent.py` | Use external prompt; handle overlap flow. |
| `backend/agent_graph/tasks_agent.py` | Use external prompt; confirmation formatting. |
| `backend/agent_graph/graph.py` | Use external chat prompt. |
| `backend/tools/calendar_tools.py` | Add times, defaults, overlap check. |
| `backend/tools/tasks_tools.py` | Return structured JSON on create. |
| `backend/run_graph.py` | Emit action SSE events. |
| `backend/tests/test_prompts.py` | Test prompt loader. |
| `backend/tests/test_overlap.py` | Test overlap detection. |
| `frontend/app/api/calendar/route.ts` | Return new time fields. |
| `frontend/app/api/chat/route.ts` | Forward action events. |
| `frontend/components/providers/QueryProvider.tsx` | React Query provider. |
| `frontend/hooks/useTasks.ts` | Fetch tasks with TanStack Query. |
| `frontend/hooks/useCalendar.ts` | Fetch events with TanStack Query. |
| `frontend/components/tasks/TaskList.tsx` | Use `useTasks` + invalidate on action. |
| `frontend/components/calendar/CalendarView.tsx` | Use `useCalendar` + invalidate on action. |
| `frontend/components/chat/ChatContext.tsx` | Expose `lastAction`; handle action events. |
| `frontend/components/chat/CreatedTaskCard.tsx` | Visual task confirmation card. |
| `frontend/components/chat/CreatedEventCard.tsx` | Visual event confirmation card. |
| `frontend/components/chat/ChatMessage.tsx` | Render cards when message has metadata. |
| `frontend/components/chat/ChatPanel.tsx` | Quick-reply buttons for agent questions. |

---

### Task 1: Add time columns to calendar schema

**Files:**
- Modify: `frontend/drizzle/schema.ts`
- Create: `frontend/drizzle/migrations/0001_add_event_times.sql`
- Modify: `frontend/drizzle/migrations/meta/_journal.json`

- [ ] **Step 1: Edit schema.ts**

```typescript
export const calendarEvents = sqliteTable("calendar_events", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  title: text("title").notNull(),
  eventDate: text("event_date").notNull(),
  eventType: text("event_type").notNull(),
  source: text("source").default("local"),
  projectId: integer("project_id").references(() => projects.id),
  startTime: text("start_time"),
  endTime: text("end_time"),
  createdAt: text("created_at").default(sql`(datetime('now'))`),
})
```

- [ ] **Step 2: Create migration SQL**

```sql
-- frontend/drizzle/migrations/0001_add_event_times.sql
ALTER TABLE calendar_events ADD COLUMN start_time TEXT DEFAULT '09:00';
ALTER TABLE calendar_events ADD COLUMN end_time TEXT DEFAULT '09:30';
```

- [ ] **Step 3: Update migration journal**

Append to `frontend/drizzle/migrations/meta/_journal.json` entries array:

```json
{
  "idx": 1,
  "version": "6",
  "when": 1750099200000,
  "tag": "0001_add_event_times",
  "breakpoints": true
}
```

Use the current epoch timestamp for `when`.

- [ ] **Step 4: Apply migration locally**

Run:
```bash
cd frontend && npx drizzle-kit migrate
```

Expected: migration applied successfully.

- [ ] **Step 5: Commit**

```bash
git add frontend/drizzle/schema.ts frontend/drizzle/migrations/
git commit -m "feat: add start_time and end_time to calendar_events"
```

---

### Task 2: Create prompt loader module

**Files:**
- Create: `backend/agent_graph/prompts/__init__.py`
- Create: `backend/agent_graph/prompts/supervisor.md`
- Create: `backend/agent_graph/prompts/tasks_agent.md`
- Create: `backend/agent_graph/prompts/tasks_agent_tools.md`
- Create: `backend/agent_graph/prompts/calendar_agent.md`
- Create: `backend/agent_graph/prompts/calendar_agent_tools.md`
- Create: `backend/agent_graph/prompts/chat_responder.md`

- [ ] **Step 1: Write prompt loader**

```python
# backend/agent_graph/prompts/__init__.py
from pathlib import Path

_PROMPT_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt from the prompts folder."""
    path = _PROMPT_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()
```

- [ ] **Step 2: Write supervisor prompt**

```markdown
# backend/agent_graph/prompts/supervisor.md
You are a supervisor for an Agile task and calendar management system.
Your only job is to route the user's message to the right specialist.

Available agents:
- tasks_agent: daily tasks, todo lists, task status, creating/updating/deleting local tasks.
- calendar_agent: deadlines, milestones, dates, calendar events, schedules.
- chat: greetings, general help, questions that are neither tasks nor calendar.

Rules:
- If a previous action is pending (the agent is waiting for an answer), keep routing to that same agent.
- Respond with ONLY the agent name: tasks_agent, calendar_agent, or chat.
- Do not add explanations or punctuation.
```

- [ ] **Step 3: Write tasks agent prompt**

```markdown
# backend/agent_graph/prompts/tasks_agent.md
You are a task management specialist for an Agile system. You help users create, list, update, and delete local tasks stored in SQLite.

Rules:
- Before creating a task, make sure you have at least the title. If the title is missing or unclear, ask the user.
- If the user does not specify priority, use "medium".
- If the user does not specify a due date, leave it empty.
- After creating a task, confirm with a friendly message that includes the task id, title, priority, status, and due date.
- If a tool returns structured JSON, use it to build the confirmation message.
- If the user asks for something ambiguous, ask for clarification.
```

- [ ] **Step 4: Write tasks agent tools description**

```markdown
# backend/agent_graph/prompts/tasks_agent_tools.md
Available tools:

- create_task(title, description="", priority="medium", due_date="", project_id=0)
  Creates a task. Priority can be low, medium, high, critical. due_date is YYYY-MM-DD.

- list_tasks(status="", project_id=0)
  Lists tasks. Optional filters: status (pending, in_progress, done) or project_id.

- update_task(task_id, status="", priority="", title="", description="", due_date="")
  Updates the provided fields of a task.

- delete_task(task_id)
  Deletes a task by id.
```

- [ ] **Step 5: Write calendar agent prompt**

```markdown
# backend/agent_graph/prompts/calendar_agent.md
You are a calendar specialist for an Agile system. You help users view and add deadlines, milestones, and other calendar events stored in SQLite.

Rules:
- Before adding an event, make sure you have at least the title and event_date.
- If the user does not specify a start time, use "09:00".
- Events default to 30 minutes, so if only a start time is given, end_time = start_time + 30 minutes.
- BEFORE inserting an event, check for overlapping events on the same date and time range.
- If an overlap is found, do NOT insert. Ask the user whether to keep the proposed time or choose a different one. Include the conflicting event details in your question.
- After adding an event, confirm with a friendly message that includes the title, date, type, start time, and end time.
- If a tool returns structured JSON, use it to build the confirmation message.
- If the user request is ambiguous, ask for clarification.
```

- [ ] **Step 6: Write calendar agent tools description**

```markdown
# backend/agent_graph/prompts/calendar_agent_tools.md
Available tools:

- get_calendar_events(start_date="", end_date="", project_id=0)
  Returns calendar events between two dates (YYYY-MM-DD).

- get_upcoming_deadlines(days=7)
  Returns deadlines within the next N days.

- add_calendar_event(title, event_date, event_type="deadline", project_id=0, start_time="", end_time="")
  Adds an event. event_type can be deadline, milestone, sprint_start, sprint_end.
  If start_time is empty it defaults to 09:00. If end_time is empty it defaults to start_time + 30 minutes.
  Returns either the created event or a conflict report.

- check_overlap(event_date, start_time, end_time)
  Returns overlapping events for the given date and time range.
```

- [ ] **Step 7: Write chat responder prompt**

```markdown
# backend/agent_graph/prompts/chat_responder.md
You are a helpful AI assistant for an Agile project management system.
Answer the user's question conversationally. Be concise and friendly.
If the user asks something that should be handled by the task or calendar specialist, suggest they ask about tasks or calendar events.
```

- [ ] **Step 8: Commit**

```bash
git add backend/agent_graph/prompts/
git commit -m "feat: add external English prompts for all agents"
```

---

### Task 3: Update calendar tools with times and overlap detection

**Files:**
- Modify: `backend/tools/calendar_tools.py`

- [ ] **Step 1: Replace calendar_tools.py content**

```python
import sqlite3
import os
import json
import logging
from datetime import datetime, timedelta
from langchain_core.tools import tool

logger = logging.getLogger("agile_agent.tools.calendar")

DB_PATH = os.getenv("DATABASE_URL", "frontend/drizzle/data.db")
if DB_PATH.startswith("file:"):
    DB_PATH = DB_PATH[5:]
logger.debug("Calendar DB path: %s", DB_PATH)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _to_minutes(time_str: str) -> int:
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


def _from_minutes(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _overlaps(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    """Return True if two [start, end) ranges overlap."""
    return a_start < b_end and b_start < a_end


def _default_times(start_time: str = "", end_time: str = ""):
    if not start_time:
        start_time = "09:00"
    if not end_time:
        end_min = _to_minutes(start_time) + 30
        end_time = _from_minutes(end_min)
    return start_time, end_time


@tool
def get_calendar_events(start_date: str = "", end_date: str = "",
                          project_id: int = 0) -> str:
    """Get calendar events. Dates in YYYY-MM-DD format. Returns deadlines and milestones."""
    logger.info("Tool get_calendar_events called — start=%s, end=%s, project=%s",
                start_date or "today", end_date or "+30d", project_id or "all")
    conn = get_db()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        start = start_date or today
        end = end_date or (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        query = "SELECT * FROM calendar_events WHERE event_date >= ? AND event_date <= ?"
        params = [start, end]
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        query += " ORDER BY event_date ASC, start_time ASC"
        rows = conn.execute(query, params).fetchall()
        if not rows:
            logger.info("get_calendar_events: no events found")
            return "No calendar events found in that period."
        logger.info("get_calendar_events: %d events returned", len(rows))
        lines = ["Calendar events:"]
        for row in rows:
            time_range = ""
            if row["start_time"] and row["end_time"]:
                time_range = f" {row['start_time']}-{row['end_time']}"
            lines.append(f"- {row['event_date']}{time_range} | {row['title']} [{row['event_type']}]")
        return "\n".join(lines)
    finally:
        conn.close()


@tool
def get_upcoming_deadlines(days: int = 7) -> str:
    """Get upcoming deadlines within the next N days (default 7)."""
    logger.info("Tool get_upcoming_deadlines called — days=%d", days)
    conn = get_db()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        rows = conn.execute(
            "SELECT * FROM calendar_events WHERE event_date >= ? AND event_date <= ? AND event_type = 'deadline' ORDER BY event_date ASC, start_time ASC",
            (today, end),
        ).fetchall()
        if not rows:
            logger.info("get_upcoming_deadlines: no deadlines in next %d days", days)
            return f"No upcoming deadlines in the next {days} days."
        logger.info("get_upcoming_deadlines: %d deadlines found", len(rows))
        lines = [f"Deadlines in the next {days} days:"]
        for row in rows:
            project = f" (project: {row['project_id']})" if row["project_id"] else ""
            time_range = ""
            if row["start_time"] and row["end_time"]:
                time_range = f" {row['start_time']}-{row['end_time']}"
            lines.append(f"- {row['event_date']}{time_range}: {row['title']}{project}")
        return "\n".join(lines)
    finally:
        conn.close()


@tool
def check_overlap(event_date: str, start_time: str = "", end_time: str = "") -> str:
    """Check for overlapping events on event_date. Times are HH:MM."""
    start_time, end_time = _default_times(start_time, end_time)
    logger.info("Tool check_overlap called — date=%s, start=%s, end=%s",
                event_date, start_time, end_time)
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM calendar_events WHERE event_date = ? ORDER BY start_time ASC",
            (event_date,),
        ).fetchall()
        conflicts = []
        for row in rows:
            if _overlaps(start_time, end_time, row["start_time"], row["end_time"]):
                conflicts.append({
                    "id": row["id"],
                    "title": row["title"],
                    "event_type": row["event_type"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                })
        if not conflicts:
            return json.dumps({"overlap": False})
        return json.dumps({"overlap": True, "conflicts": conflicts})
    finally:
        conn.close()


@tool
def add_calendar_event(title: str, event_date: str, event_type: str = "deadline",
                        project_id: int = 0, start_time: str = "", end_time: str = "") -> str:
    """Add a calendar event. event_type: deadline, milestone, sprint_start, sprint_end.
    If start_time is empty defaults to 09:00. If end_time is empty defaults to start_time + 30 min.
    Returns the created event or a conflict report."""
    start_time, end_time = _default_times(start_time, end_time)
    logger.info("Tool add_calendar_event called — title=%s, date=%s, type=%s, project=%s, %s-%s",
                title[:100], event_date, event_type, project_id or "none", start_time, end_time)

    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM calendar_events WHERE event_date = ?",
            (event_date,),
        ).fetchall()
        for row in rows:
            if _overlaps(start_time, end_time, row["start_time"], row["end_time"]):
                conflict = {
                    "id": row["id"],
                    "title": row["title"],
                    "event_type": row["event_type"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                }
                logger.info("add_calendar_event: overlap with event %d", row["id"])
                return json.dumps({
                    "success": False,
                    "reason": "overlap",
                    "conflict": conflict,
                    "message": f"Overlaps with '{row['title']}' ({row['start_time']}-{row['end_time']})."
                })

        cur = conn.execute(
            "INSERT INTO calendar_events (title, event_date, event_type, project_id, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?)",
            (title, event_date, event_type, project_id or None, start_time, end_time),
        )
        conn.commit()
        event_id = cur.lastrowid
        logger.info("add_calendar_event: event '%s' added on %s id=%d", title, event_date, event_id)
        return json.dumps({
            "success": True,
            "event": {
                "id": event_id,
                "title": title,
                "event_date": event_date,
                "event_type": event_type,
                "project_id": project_id or None,
                "start_time": start_time,
                "end_time": end_time,
            }
        })
    finally:
        conn.close()


calendar_tools = [get_calendar_events, get_upcoming_deadlines, check_overlap, add_calendar_event]
```

- [ ] **Step 2: Commit**

```bash
git add backend/tools/calendar_tools.py
git commit -m "feat: calendar tools support time ranges and overlap detection"
```

---

### Task 4: Update tasks tool to return structured data

**Files:**
- Modify: `backend/tools/tasks_tools.py`

- [ ] **Step 1: Modify create_task return value**

In `create_task`, replace the return statement with:

```python
return json.dumps({
    "success": True,
    "task": {
        "id": task_id,
        "title": title,
        "description": description,
        "status": "pending",
        "priority": priority,
        "due_date": due_date or None,
        "project_id": project_id or None,
    }
}, ensure_ascii=False)
```

Add `import json` at the top of the file if not present.

- [ ] **Step 2: Commit**

```bash
git add backend/tools/tasks_tools.py
git commit -m "feat: create_task returns structured JSON confirmation"
```

---

### Task 5: Extend agent state with pending_action

**Files:**
- Modify: `backend/agent_graph/state.py`

- [ ] **Step 1: Update state.py**

```python
import logging
from typing import TypedDict, List, Optional, Any, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

logger = logging.getLogger("agile_agent.state")


class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    current_agent: Optional[str]
    context: dict[str, Any]
    pending_action: Optional[dict]
```

- [ ] **Step 2: Commit**

```bash
git add backend/agent_graph/state.py
git commit -m "feat: add pending_action to AgentState"
```

---

### Task 6: Update supervisor to respect pending_action

**Files:**
- Modify: `backend/agent_graph/supervisor.py`

- [ ] **Step 1: Load external prompt and check pending_action**

Replace the imports and prompt definition with:

```python
import logging
from langchain_core.prompts import ChatPromptTemplate
from .llm import create_llm, invoke_with_retry, get_fallback_model_name, is_rate_limited
from .state import AgentState
from .utils import extract_text
from .prompts import load_prompt

logger = logging.getLogger("agile_agent.supervisor")

SUPERVISOR_PROMPT = load_prompt("supervisor")
```

In `route_to_agent`, add at the top:

```python
def route_to_agent(state: AgentState) -> str:
    pending = state.get("pending_action")
    if pending and pending.get("agent") in {"tasks_agent", "calendar_agent", "chat"}:
        logger.info("Supervisor honoring pending_action — agent=%s", pending["agent"])
        return pending["agent"]

    messages = state["messages"]
    ...
```

- [ ] **Step 2: Commit**

```bash
git add backend/agent_graph/supervisor.py
git commit -m "feat: supervisor routes back to pending agent and loads external prompt"
```

---

### Task 7: Refactor calendar agent with external prompt and action handling

**Files:**
- Modify: `backend/agent_graph/calendar_agent.py`

- [ ] **Step 1: Replace calendar_agent.py**

```python
import json
import logging
from datetime import datetime, timedelta
from langchain_core.messages import SystemMessage, AIMessage
from .llm import create_llm, invoke_with_retry, get_fallback_model_name, is_rate_limited
from ..tools.calendar_tools import calendar_tools
from .state import AgentState
from .utils import extract_text
from .prompts import load_prompt

logger = logging.getLogger("agile_agent.calendar_agent")

CALENDAR_AGENT_PROMPT = load_prompt("calendar_agent") + "\n\n" + load_prompt("calendar_agent_tools")


def create_calendar_agent():
    llm = create_llm(temperature=0)
    logger.debug("Calendar agent created with tools: %s", [t.name for t in calendar_tools])
    return llm.bind_tools(calendar_tools)


def _build_pending_action(tool_result: dict) -> dict:
    return {
        "agent": "calendar_agent",
        "type": "confirm_overlap",
        "conflict": tool_result.get("conflict"),
        "proposed": tool_result.get("proposed"),
    }


def handle_calendar(state: AgentState) -> AgentState:
    messages = state["messages"]
    session_id = state.get("context", {}).get("session_id", "")
    last_message = messages[-1].content if messages else ""
    logger.info(
        "Calendar agent invoked — session_id=%s, history=%d, last_message=%s",
        session_id or "n/a",
        len(messages),
        last_message[:200] if isinstance(last_message, str) else str(last_message)[:200],
    )
    try:
        agent = create_calendar_agent()
        system_msg = SystemMessage(content=CALENDAR_AGENT_PROMPT)
        response = invoke_with_retry(agent, [system_msg] + messages)
        tool_calls = getattr(response, "tool_calls", None)
        logger.info(
            "Calendar agent response — session_id=%s, content_length=%d, tool_calls=%s",
            session_id or "n/a",
            len(extract_text(response.content)),
            len(tool_calls) if tool_calls else 0,
        )
        return {**state, "current_agent": "calendar_agent", "messages": state["messages"] + [response]}
    except Exception as e:
        logger.error("Calendar agent error — session_id=%s, error=%s", session_id or "n/a", e)
        if is_rate_limited(e):
            fallback_model = get_fallback_model_name()
            if fallback_model:
                try:
                    fallback_llm = create_llm(model=fallback_model, temperature=0)
                    fallback_agent = fallback_llm.bind_tools(calendar_tools)
                    response = invoke_with_retry(fallback_agent, [system_msg] + messages)
                    logger.info("Calendar agent response via fallback %s", fallback_model)
                    return {**state, "current_agent": "calendar_agent", "messages": state["messages"] + [response]}
                except Exception as e2:
                    logger.error("Fallback calendar agent also failed: %s", e2)
        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content="Sorry, I couldn't connect to the AI assistant. Please check that GOOGLE_API_KEY is set in backend/.env or that the API quota is not exhausted.")
            ],
        }
```

- [ ] **Step 2: Commit**

```bash
git add backend/agent_graph/calendar_agent.py
git commit -m "feat: calendar agent uses external prompt and English errors"
```

---

### Task 8: Refactor tasks agent with external prompt

**Files:**
- Modify: `backend/agent_graph/tasks_agent.py`

- [ ] **Step 1: Replace tasks_agent.py**

```python
import logging
from langchain_core.messages import SystemMessage, AIMessage
from .llm import create_llm, invoke_with_retry, get_fallback_model_name, is_rate_limited
from ..tools.tasks_tools import tasks_tools
from .state import AgentState
from .utils import extract_text
from .prompts import load_prompt

logger = logging.getLogger("agile_agent.tasks_agent")

TASKS_AGENT_PROMPT = load_prompt("tasks_agent") + "\n\n" + load_prompt("tasks_agent_tools")


def create_tasks_agent():
    llm = create_llm(temperature=0)
    logger.debug("Tasks agent created with tools: %s", [t.name for t in tasks_tools])
    return llm.bind_tools(tasks_tools)


def handle_tasks(state: AgentState) -> AgentState:
    messages = state["messages"]
    session_id = state.get("context", {}).get("session_id", "")
    last_message = messages[-1].content if messages else ""
    logger.info(
        "Tasks agent invoked — session_id=%s, history=%d, last_message=%s",
        session_id or "n/a",
        len(messages),
        last_message[:200] if isinstance(last_message, str) else str(last_message)[:200],
    )
    try:
        agent = create_tasks_agent()
        system_msg = SystemMessage(content=TASKS_AGENT_PROMPT)
        response = invoke_with_retry(agent, [system_msg] + messages)
        tool_calls = getattr(response, "tool_calls", None)
        logger.info(
            "Tasks agent response — session_id=%s, content_length=%d, tool_calls=%s",
            session_id or "n/a",
            len(extract_text(response.content)),
            len(tool_calls) if tool_calls else 0,
        )
        return {**state, "current_agent": "tasks_agent", "messages": state["messages"] + [response]}
    except Exception as e:
        logger.error("Tasks agent error — session_id=%s, error=%s", session_id or "n/a", e)
        if is_rate_limited(e):
            fallback_model = get_fallback_model_name()
            if fallback_model:
                try:
                    fallback_llm = create_llm(model=fallback_model, temperature=0)
                    fallback_agent = fallback_llm.bind_tools(tasks_tools)
                    response = invoke_with_retry(fallback_agent, [system_msg] + messages)
                    logger.info("Tasks agent response via fallback %s", fallback_model)
                    return {**state, "current_agent": "tasks_agent", "messages": state["messages"] + [response]}
                except Exception as e2:
                    logger.error("Fallback tasks agent also failed: %s", e2)
        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content="Sorry, I couldn't connect to the AI assistant. Please check that GOOGLE_API_KEY is set in backend/.env or that the API quota is not exhausted.")
            ],
        }
```

- [ ] **Step 2: Commit**

```bash
git add backend/agent_graph/tasks_agent.py
git commit -m "feat: tasks agent uses external prompt and English errors"
```

---

### Task 9: Update graph to use external chat prompt

**Files:**
- Modify: `backend/agent_graph/graph.py`

- [ ] **Step 1: Replace CHAT_PROMPT definition**

```python
from .prompts import load_prompt

CHAT_PROMPT = load_prompt("chat_responder")
```

Remove the old inline string.

- [ ] **Step 2: Commit**

```bash
git add backend/agent_graph/graph.py
git commit -m "feat: chat responder loads external prompt"
```

---

### Task 10: Emit structured action events from run_graph.py

**Files:**
- Modify: `backend/run_graph.py`

- [ ] **Step 1: Update run_graph.py to emit action events**

Replace the main result handling block with:

```python
import json
import sys
import logging

sys.path.insert(0, ".")

from backend.agent_graph.logging_config import configure_logging
configure_logging()

from backend.agent_graph.graph import graph
from backend.agent_graph.utils import extract_text
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

logger = logging.getLogger("run_graph")


def _messages_to_dict(messages):
    out = []
    for m in messages:
        entry = {"role": getattr(m, "type", "unknown"), "content": ""}
        content = getattr(m, "content", "")
        if isinstance(content, str):
            entry["content"] = content
        elif isinstance(content, list):
            entry["content"] = str(content)
        tool_calls = getattr(m, "tool_calls", None)
        if tool_calls:
            entry["tool_calls"] = tool_calls
        out.append(entry)
    return out


def _try_parse_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def _emit(action: str, payload: dict):
    print(json.dumps({"type": "action", "action": action, **payload}), flush=True)


def main():
    raw = sys.stdin.read()
    if not raw:
        logger.error("No input received on stdin")
        print(json.dumps({"error": "No input received"}))
        sys.exit(1)

    try:
        input_data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON input: %s", e)
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    message = input_data.get("message", "")
    previous_messages = input_data.get("previous_messages", [])
    session_id = input_data.get("session_id", "")

    logger.info(
        "Received chat request — session_id=%s, previous_messages=%d, message_length=%d",
        session_id or "n/a",
        len(previous_messages),
        len(message),
    )

    messages = []
    for prev in previous_messages:
        role = prev.get("role")
        content = prev.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=message))

    state = {
        "messages": messages,
        "current_agent": None,
        "context": {"session_id": session_id},
        "pending_action": input_data.get("pending_action"),
    }

    logger.info(
        "Invoking graph — session_id=%s, total_messages=%d",
        session_id or "n/a",
        len(messages),
    )

    try:
        result = graph.invoke(state)
        final_agent = result.get("current_agent", "unknown")
        print(json.dumps({"type": "agent", "agent": final_agent}), flush=True)

        # Detect creation actions from tool results
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage):
                parsed = _try_parse_json(msg.content)
                if isinstance(parsed, dict) and parsed.get("success"):
                    if "task" in parsed:
                        _emit("created", {"entity": "task", "data": parsed["task"]})
                    elif "event" in parsed:
                        _emit("created", {"entity": "calendar_event", "data": parsed["event"]})
                elif isinstance(parsed, dict) and parsed.get("reason") == "overlap":
                    _emit("confirm_overlap", {
                        "entity": "calendar_event",
                        "message": parsed.get("message"),
                        "conflict": parsed.get("conflict"),
                    })

        last_msg = result["messages"][-1]
        output = extract_text(last_msg.content)
        print(json.dumps({"type": "chunk", "content": output}), flush=True)

        logger.info(
            "Graph completed — session_id=%s, final_agent=%s, output_length=%d",
            session_id or "n/a",
            final_agent,
            len(output),
        )
    except Exception as e:
        logger.exception("Graph invocation failed — session_id=%s", session_id or "n/a")
        print(json.dumps({"type": "error", "error": str(e)}), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add backend/run_graph.py
git commit -m "feat: emit structured action events from chat runner"
```

---

### Task 11: Add backend tests

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_overlap.py`
- Create: `backend/tests/test_prompts.py`

- [ ] **Step 1: Create tests directory and overlap tests**

```python
# backend/tests/test_overlap.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.calendar_tools import _overlaps, _default_times


def test_no_overlap():
    assert _overlaps("09:00", "09:30", "10:00", "10:30") is False
    assert _overlaps("10:00", "10:30", "09:00", "09:30") is False


def test_partial_overlap():
    assert _overlaps("09:00", "10:00", "09:30", "10:30") is True


def test_full_containment():
    assert _overlaps("09:00", "11:00", "09:30", "10:30") is True


def test_adjacent_no_overlap():
    assert _overlaps("09:00", "09:30", "09:30", "10:00") is False


def test_default_times():
    start, end = _default_times("", "")
    assert start == "09:00"
    assert end == "09:30"
    start, end = _default_times("14:00", "")
    assert end == "14:30"
```

- [ ] **Step 2: Create prompt loader test**

```python
# backend/tests/test_prompts.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_graph.prompts import load_prompt


def test_load_existing_prompts():
    for name in ["supervisor", "tasks_agent", "calendar_agent", "chat_responder"]:
        text = load_prompt(name)
        assert isinstance(text, str)
        assert len(text) > 20


def test_load_missing_prompt_raises():
    try:
        load_prompt("nonexistent_prompt_xyz")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass
```

- [ ] **Step 3: Run tests**

```bash
cd backend && . venv/bin/activate && python -m pytest tests/ -v
```

Expected: all 7 tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/
git commit -m "test: add overlap detection and prompt loader tests"
```

---

### Task 12: Update frontend calendar API to expose time fields

**Files:**
- Modify: `frontend/app/api/calendar/route.ts`

- [ ] **Step 1: Ensure POST accepts and returns new fields**

The existing POST already forwards body fields. Update the GET to keep returning all columns. No code change needed beyond ensuring the schema migration is applied. Verify the route returns `startTime` and `endTime`.

Add a small comment if desired.

- [ ] **Step 2: Commit**

```bash
git add frontend/app/api/calendar/route.ts
git commit -m "chore: calendar api ready for start/end time fields"
```

---

### Task 13: Set up TanStack Query provider and data hooks

**Files:**
- Create: `frontend/components/providers/QueryProvider.tsx`
- Create: `frontend/hooks/useTasks.ts`
- Create: `frontend/hooks/useCalendar.ts`
- Modify: `frontend/app/layout.tsx`

- [ ] **Step 1: Create QueryProvider**

```tsx
// frontend/components/providers/QueryProvider.tsx
"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient())
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}
```

- [ ] **Step 2: Create useTasks hook**

```tsx
// frontend/hooks/useTasks.ts
"use client"

import { useQuery, useQueryClient } from "@tanstack/react-query"

export interface Task {
  id: number
  title: string
  description: string
  status: string
  priority: string
  dueDate: string | null
  projectId: number | null
}

const TASKS_KEY = ["tasks"]

export function useTasks(status?: string, projectId?: number) {
  return useQuery<Task[]>({
    queryKey: TASKS_KEY,
    queryFn: async () => {
      const params = new URLSearchParams()
      if (status) params.set("status", status)
      if (projectId) params.set("project_id", String(projectId))
      const res = await fetch(`/api/tasks?${params.toString()}`)
      const data = await res.json()
      return data.tasks
    },
  })
}

export function useInvalidateTasks() {
  const client = useQueryClient()
  return () => client.invalidateQueries({ queryKey: TASKS_KEY })
}
```

- [ ] **Step 3: Create useCalendar hook**

```tsx
// frontend/hooks/useCalendar.ts
"use client"

import { useQuery, useQueryClient } from "@tanstack/react-query"

export interface CalendarEvent {
  id: number
  title: string
  eventDate: string
  eventType: string
  source: string
  projectId: number | null
  startTime: string | null
  endTime: string | null
}

const CALENDAR_KEY = ["calendar"]

export function useCalendar(startDate?: string, endDate?: string) {
  return useQuery<CalendarEvent[]>({
    queryKey: CALENDAR_KEY,
    queryFn: async () => {
      const params = new URLSearchParams()
      if (startDate) params.set("start_date", startDate)
      if (endDate) params.set("end_date", endDate)
      const res = await fetch(`/api/calendar?${params.toString()}`)
      const data = await res.json()
      return data.events
    },
  })
}

export function useInvalidateCalendar() {
  const client = useQueryClient()
  return () => client.invalidateQueries({ queryKey: CALENDAR_KEY })
}
```

- [ ] **Step 4: Wrap app with QueryProvider**

Edit `frontend/app/layout.tsx`:

```tsx
import { QueryProvider } from "@/components/providers/QueryProvider"
```

Wrap the `ToastProvider` children with `QueryProvider`:

```tsx
<QueryProvider>
  <ToastProvider>
    ...
  </ToastProvider>
</QueryProvider>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/components/providers/QueryProvider.tsx frontend/hooks/useTasks.ts frontend/hooks/useCalendar.ts frontend/app/layout.tsx
git commit -m "feat: add tanstack query provider and data hooks"
```

---

### Task 14: Update TaskList to use React Query

**Files:**
- Modify: `frontend/components/tasks/TaskList.tsx`

- [ ] **Step 1: Rewrite TaskList**

```tsx
"use client"

import { useTasks } from "@/hooks/useTasks"
import { TaskCard } from "./TaskCard"

export function TaskList() {
  const { data: tasks, isLoading } = useTasks()

  if (isLoading) return <div className="p-4">Loading tasks...</div>

  return (
    <div className="space-y-3">
      {tasks?.map((task) => (
        <TaskCard key={task.id} {...task} />
      ))}
      {tasks?.length === 0 && <p className="text-muted-foreground">No tasks yet.</p>}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/tasks/TaskList.tsx
git commit -m "feat: TaskList uses tanstack query"
```

---

### Task 15: Update CalendarView to use React Query and show times

**Files:**
- Modify: `frontend/components/calendar/CalendarView.tsx`

- [ ] **Step 1: Rewrite CalendarView**

```tsx
"use client"

import { useCalendar } from "@/hooks/useCalendar"
import { GlassCard } from "@/components/ui/glass-card"
import { CalendarDays, Clock } from "lucide-react"

export function CalendarView() {
  const { data: events, isLoading } = useCalendar()

  const grouped = events?.reduce<Record<string, typeof events>>((acc, event) => {
    const key = event.eventDate
    if (!acc[key]) acc[key] = []
    acc[key].push(event)
    return acc
  }, {}) || {}

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading calendar...</p>

  if (!events || events.length === 0) return <p className="text-sm text-muted-foreground">No calendar events.</p>

  return (
    <div className="space-y-4">
      {Object.entries(grouped).sort().map(([date, dateEvents]) => (
        <GlassCard key={date}>
          <div className="flex items-center gap-2 mb-3">
            <CalendarDays className="h-4 w-4 text-primary" />
            <h3 className="font-semibold text-sm">{date}</h3>
          </div>
          <ul className="space-y-2">
            {dateEvents.map((event) => (
              <li key={event.id} className="flex items-center gap-3 rounded-lg border border-border/30 bg-background/40 px-3 py-2">
                <span className={`h-2 w-2 shrink-0 rounded-full ${
                  event.eventType === "deadline" ? "bg-destructive" :
                  event.eventType === "milestone" ? "bg-blue-500" :
                  "bg-green-500"
                }`} />
                <span className="text-sm font-medium">{event.title}</span>
                {event.startTime && event.endTime && (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {event.startTime} - {event.endTime}
                  </span>
                )}
                <span className="text-xs text-muted-foreground">({event.eventType})</span>
              </li>
            ))}
          </ul>
        </GlassCard>
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/calendar/CalendarView.tsx
git commit -m "feat: CalendarView uses tanstack query and shows time ranges"
```

---

### Task 16: Extend ChatContext to handle action events

**Files:**
- Modify: `frontend/components/chat/ChatContext.tsx`

- [ ] **Step 1: Add ChatAction type and lastAction state**

```tsx
export interface ChatAction {
  type: "created" | "needs_info" | "confirm_overlap"
  entity?: "task" | "calendar_event"
  message?: string
  alternatives?: string[]
  conflicts?: Record<string, unknown>[]
  data?: Record<string, unknown>
}

export interface Message {
  role: "user" | "assistant"
  content: string
  agent?: string
  error?: boolean
  action?: ChatAction
}
```

- [ ] **Step 2: Expose lastAction and allow passing pending_action to sendMessage**

```tsx
interface ChatContextValue {
  messages: Message[]
  streamingContent: string
  isLoading: boolean
  isOpen: boolean
  activeAgent: string | null
  error: string | null
  lastAction: ChatAction | null
  sendMessage: (text: string) => Promise<void>
  togglePanel: () => void
  closePanel: () => void
  clearError: () => void
}
```

Add state:

```tsx
const [lastAction, setLastAction] = useState<ChatAction | null>(null)
const pendingActionRef = useRef<ChatAction | null>(null)
```

Update `sendMessage` to include `pending_action` in the request body and reset it after sending:

```tsx
body: JSON.stringify({
  message,
  session_id: sessionId.current,
  previous_messages: messagesRef.current,
  pending_action: pendingActionRef.current,
}),
```

And after sending:

```tsx
pendingActionRef.current = null
setLastAction(null)
```

In the event parsing loop, when `event.type === "action"`, set:

```tsx
const action: ChatAction = {
  type: event.action,
  entity: event.entity,
  message: event.message,
  alternatives: event.alternatives,
  conflicts: event.conflicts,
  data: event.data,
}
setLastAction(action)
pendingActionRef.current = action
```

When the final assistant message is stored, attach the action:

```tsx
setMessages((prev) => [
  ...prev,
  {
    role: "assistant",
    content: streamingRef.current,
    agent: activeAgentRef.current || undefined,
    action: pendingActionRef.current || undefined,
  },
])
```

- [ ] **Step 3: Commit**

```bash
git add frontend/components/chat/ChatContext.tsx
git commit -m "feat: chat context handles structured action events"
```

---

### Task 17: Create visual confirmation cards

**Files:**
- Create: `frontend/components/chat/CreatedTaskCard.tsx`
- Create: `frontend/components/chat/CreatedEventCard.tsx`

- [ ] **Step 1: Create CreatedTaskCard**

```tsx
// frontend/components/chat/CreatedTaskCard.tsx
import { CheckCircle2 } from "lucide-react"

interface CreatedTaskCardProps {
  data: Record<string, unknown>
}

export function CreatedTaskCard({ data }: CreatedTaskCardProps) {
  return (
    <div className="rounded-xl border border-primary/20 bg-primary/10 px-4 py-3 my-2">
      <div className="flex items-center gap-2 mb-2">
        <CheckCircle2 className="h-4 w-4 text-primary" />
        <span className="text-xs font-semibold uppercase tracking-wider text-primary">Task created</span>
      </div>
      <div className="space-y-1 text-sm">
        <p><span className="text-muted-foreground">Title:</span> {String(data.title || "—")}</p>
        <p><span className="text-muted-foreground">Priority:</span> {String(data.priority || "—")}</p>
        <p><span className="text-muted-foreground">Status:</span> {String(data.status || "—")}</p>
        {data.due_date && <p><span className="text-muted-foreground">Due:</span> {String(data.due_date)}</p>}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create CreatedEventCard**

```tsx
// frontend/components/chat/CreatedEventCard.tsx
import { CalendarDays } from "lucide-react"

interface CreatedEventCardProps {
  data: Record<string, unknown>
}

export function CreatedEventCard({ data }: CreatedEventCardProps) {
  return (
    <div className="rounded-xl border border-blue-500/20 bg-blue-500/10 px-4 py-3 my-2">
      <div className="flex items-center gap-2 mb-2">
        <CalendarDays className="h-4 w-4 text-blue-500" />
        <span className="text-xs font-semibold uppercase tracking-wider text-blue-500">Event created</span>
      </div>
      <div className="space-y-1 text-sm">
        <p><span className="text-muted-foreground">Title:</span> {String(data.title || "—")}</p>
        <p><span className="text-muted-foreground">Date:</span> {String(data.event_date || "—")}</p>
        <p><span className="text-muted-foreground">Type:</span> {String(data.event_type || "—")}</p>
        {data.start_time && data.end_time && (
          <p><span className="text-muted-foreground">Time:</span> {String(data.start_time)} - {String(data.end_time)}</p>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/components/chat/CreatedTaskCard.tsx frontend/components/chat/CreatedEventCard.tsx
git commit -m "feat: add created task and event cards"
```

---

### Task 18: Render cards inside chat messages

**Files:**
- Modify: `frontend/components/chat/ChatMessage.tsx`

- [ ] **Step 1: Import cards and render when action is created**

```tsx
import { cn } from "@/lib/utils"
import { AlertCircle } from "lucide-react"
import { getAgentLabel, ChatAction } from "./ChatContext"
import { CreatedTaskCard } from "./CreatedTaskCard"
import { CreatedEventCard } from "./CreatedEventCard"

interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
  agent?: string
  error?: boolean
  action?: ChatAction
}

export function ChatMessage({ role, content, agent, error, action }: ChatMessageProps) {
  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"} mb-4`}>
      <div className="max-w-[80%]">
        {role === "assistant" && (
          <div className="mb-1 flex items-center gap-1.5 px-1">
            <span
              className={cn(
                "text-[10px] uppercase tracking-wider font-medium",
                error ? "text-destructive" : "text-muted-foreground"
              )}
            >
              {error ? "Error" : getAgentLabel(agent)}
            </span>
          </div>
        )}
        <div
          className={cn(
            "rounded-xl px-4 py-2.5 text-sm backdrop-blur-sm border",
            role === "user"
              ? "border-primary/20 bg-primary/15 text-foreground"
              : error
              ? "border-destructive/30 bg-destructive/10 text-destructive"
              : "border-border/30 bg-muted/30 text-foreground"
          )}
        >
          <div className="flex items-start gap-2">
            {error && <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />}
            <p className="whitespace-pre-wrap">{content}</p>
          </div>
        </div>
        {action?.type === "created" && action.entity === "task" && (
          <CreatedTaskCard data={action.data || {}} />
        )}
        {action?.type === "created" && action.entity === "calendar_event" && (
          <CreatedEventCard data={action.data || {}} />
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/chat/ChatMessage.tsx
git commit -m "feat: render created cards inside chat messages"
```

---

### Task 19: Wire view refresh to chat actions

**Files:**
- Modify: `frontend/components/tasks/TaskList.tsx`
- Modify: `frontend/components/calendar/CalendarView.tsx`

- [ ] **Step 1: Add invalidation to TaskList**

```tsx
"use client"

import { useEffect } from "react"
import { useTasks, useInvalidateTasks } from "@/hooks/useTasks"
import { TaskCard } from "./TaskCard"
import { useChat } from "@/components/chat/ChatContext"

export function TaskList() {
  const { data: tasks, isLoading } = useTasks()
  const invalidate = useInvalidateTasks()
  const { lastAction } = useChat()

  useEffect(() => {
    if (lastAction?.type === "created" && lastAction.entity === "task") {
      invalidate()
    }
  }, [lastAction, invalidate])

  if (isLoading) return <div className="p-4">Loading tasks...</div>

  return (
    <div className="space-y-3">
      {tasks?.map((task) => (
        <TaskCard key={task.id} {...task} />
      ))}
      {tasks?.length === 0 && <p className="text-muted-foreground">No tasks yet.</p>}
    </div>
  )
}
```

- [ ] **Step 2: Add invalidation to CalendarView**

```tsx
"use client"

import { useEffect } from "react"
import { useCalendar, useInvalidateCalendar } from "@/hooks/useCalendar"
import { useChat } from "@/components/chat/ChatContext"
import { GlassCard } from "@/components/ui/glass-card"
import { CalendarDays, Clock } from "lucide-react"

export function CalendarView() {
  const { data: events, isLoading } = useCalendar()
  const invalidate = useInvalidateCalendar()
  const { lastAction } = useChat()

  useEffect(() => {
    if (lastAction?.type === "created" && lastAction.entity === "calendar_event") {
      invalidate()
    }
  }, [lastAction, invalidate])

  const grouped = events?.reduce<Record<string, typeof events>>((acc, event) => {
    const key = event.eventDate
    if (!acc[key]) acc[key] = []
    acc[key].push(event)
    return acc
  }, {}) || {}

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading calendar...</p>

  if (!events || events.length === 0) return <p className="text-sm text-muted-foreground">No calendar events.</p>

  return (
    <div className="space-y-4">
      {Object.entries(grouped).sort().map(([date, dateEvents]) => (
        <GlassCard key={date}>
          <div className="flex items-center gap-2 mb-3">
            <CalendarDays className="h-4 w-4 text-primary" />
            <h3 className="font-semibold text-sm">{date}</h3>
          </div>
          <ul className="space-y-2">
            {dateEvents.map((event) => (
              <li key={event.id} className="flex items-center gap-3 rounded-lg border border-border/30 bg-background/40 px-3 py-2">
                <span className={`h-2 w-2 shrink-0 rounded-full ${
                  event.eventType === "deadline" ? "bg-destructive" :
                  event.eventType === "milestone" ? "bg-blue-500" :
                  "bg-green-500"
                }`} />
                <span className="text-sm font-medium">{event.title}</span>
                {event.startTime && event.endTime && (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {event.startTime} - {event.endTime}
                  </span>
                )}
                <span className="text-xs text-muted-foreground">({event.eventType})</span>
              </li>
            ))}
          </ul>
        </GlassCard>
      ))}
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/components/tasks/TaskList.tsx frontend/components/calendar/CalendarView.tsx
git commit -m "feat: views refresh when chat creates matching entity"
```

---

### Task 20: Add quick-reply buttons for agent questions

**Files:**
- Modify: `frontend/components/chat/ChatPanel.tsx`
- Modify: `frontend/components/chat/ChatMessage.tsx`

- [ ] **Step 1: Render quick replies in ChatPanel**

Use `lastAction` from `useChat()` to show buttons above the input.

```tsx
const { messages, streamingContent, isLoading, isOpen, togglePanel, sendMessage, activeAgent, error, lastAction } = useChat()
```

Add above `ChatInput`:

```tsx
{lastAction && (lastAction.type === "needs_info" || lastAction.type === "confirm_overlap") && (
  <div className="mb-2 flex flex-wrap gap-2">
    {lastAction.type === "confirm_overlap" && (
      <>
        <button
          onClick={() => sendMessage("Keep it at the same time")}
          className="rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground hover:bg-primary/90"
        >
          Keep same time
        </button>
        <button
          onClick={() => sendMessage("Find another time")}
          className="rounded-md border border-border/40 bg-background px-3 py-1.5 text-xs hover:bg-accent"
        >
          Find another time
        </button>
      </>
    )}
    {lastAction.type === "needs_info" && lastAction.alternatives?.map((alt) => (
      <button
        key={alt}
        onClick={() => sendMessage(alt)}
        className="rounded-md border border-border/40 bg-background px-3 py-1.5 text-xs hover:bg-accent"
      >
        {alt}
      </button>
    ))}
  </div>
)}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/chat/ChatPanel.tsx
git commit -m "feat: quick reply buttons for agent questions and overlaps"
```

---

### Task 21: Ensure chat API forwards pending_action

**Files:**
- Modify: `frontend/app/api/chat/route.ts`

- [ ] **Step 1: Update payload interface and stdin write**

```tsx
interface ChatPayload {
  message: string
  previous_messages?: { role: string; content: string }[]
  session_id?: string
  pending_action?: Record<string, unknown>
}
```

Forward `pending_action`:

```tsx
const { message, previous_messages, session_id, pending_action } = (await req.json()) as ChatPayload
```

```tsx
python.stdin.write(
  JSON.stringify({
    message,
    session_id,
    previous_messages: previous_messages || [],
    pending_action: pending_action || null,
  })
)
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/api/chat/route.ts
git commit -m "feat: forward pending_action to chat runner"
```

---

### Task 22: Run full integration check

**Files:**
- None (verification only)

- [ ] **Step 1: Run backend tests**

```bash
cd backend && . venv/bin/activate && python -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 2: Run frontend type check / lint**

```bash
cd frontend && npm run lint
```

Expected: no new errors.

- [ ] **Step 3: Start dev server and test chat flows**

Terminal 1:
```bash
make dev
```

Test scenarios in the browser:
1. Create a task via chat → see confirmation card and TaskList refresh.
2. Create a calendar event via chat → see confirmation card and CalendarView refresh.
3. Create two overlapping calendar events → see overlap question and quick replies.
4. Create a task without title → agent asks for title, user answers, task is created.

- [ ] **Step 4: Commit any final fixes**

```bash
git add -A
git commit -m "fix: integration adjustments"
```

---

## Self-review checklist

- **Spec coverage:**
  - Time columns & defaults → Task 1, Task 3.
  - External English prompts → Task 2, Tasks 6-9.
  - Structured SSE events → Task 10.
  - Confirmation cards in chat → Tasks 17-18.
  - Selective view refresh → Tasks 13-15, 19.
  - Multi-turn questions → Tasks 5-6, 16, 20-21.
  - Calendar overlap detection → Task 3, Task 7, Task 20.
  - Tests → Task 11.
- **Placeholder scan:** No TBD/TODO or vague steps found.
- **Type consistency:** `ChatAction` fields match usage across Context, Message, ChatPanel, and run_graph payloads.
