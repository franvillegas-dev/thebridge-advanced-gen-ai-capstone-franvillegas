# Chat confirmations, agent prompts refactor and calendar overlap detection — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the chat return rich confirmation cards for created tasks/events, refresh related views automatically, move agent prompts to a dedicated folder, and detect calendar event overlaps before creation.

**Architecture:** Agent prompts move to `backend/agent_graph/prompts/*.md` and are loaded by a small helper. The chat response becomes a structured JSON with `content`, `agent`, `created_entity` and `refresh`. A lightweight pubsub module refreshes dashboard/task/calendar views. Calendar overlap detection is implemented as a separate tool plus an `allow_overlap` flag on `add_calendar_event`.

**Tech Stack:** Python 3.11, LangGraph/LangChain, SQLite, Next.js 16, TypeScript, React 19, Tailwind CSS v4.

---

## File map

| File | Responsibility |
|---|---|
| `backend/agent_graph/prompts/*.md` | Agent prompts (one per agent). |
| `backend/agent_graph/prompts.py` | Loader that reads prompt files into module constants. |
| `backend/agent_graph/supervisor.py` | Uses loaded supervisor prompt. |
| `backend/agent_graph/tasks_agent.py` | Uses loaded tasks agent prompt. |
| `backend/agent_graph/calendar_agent.py` | Uses loaded calendar agent prompt. |
| `backend/agent_graph/graph.py` | Uses loaded chat prompt. |
| `backend/tools/calendar_tools.py` | Adds `check_calendar_overlap` and `start_time`/`end_time` support. |
| `backend/agent_graph/utils.py` | Helpers to parse tool results and build `created_entity`. |
| `backend/run_graph.py` | Returns structured JSON including `created_entity` and `refresh`. |
| `frontend/app/api/chat/route.ts` | Passes through the structured JSON. |
| `frontend/lib/events.ts` | Pubsub for view refresh events. |
| `frontend/components/chat/ChatContext.tsx` | Parses structured response and emits refresh events. |
| `frontend/components/chat/CreatedEntityCard.tsx` | Renders task/calendar confirmation cards. |
| `frontend/components/chat/ChatMessage.tsx` | Displays the card when present. |
| `frontend/components/dashboard/DashboardHome.tsx` | Subscribes to refresh events. |
| `frontend/components/tasks/TaskList.tsx` | Subscribes to refresh events. |
| `frontend/components/calendar/CalendarView.tsx` | Subscribes to refresh events. |

---

### Task 1: Add pytest to the backend

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/tests/__init__.py`

- [ ] **Step 1: Add pytest to requirements**

Add the test dependency to `backend/requirements.txt`:

```text
langgraph>=0.2.0
langchain>=0.3.0
langchain-community>=0.3.0
langchain-google-genai>=2.0.0
langchain-core>=0.3.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pytest>=8.0.0
```

- [ ] **Step 2: Install pytest in the virtual environment**

Run:

```bash
cd /Users/franvillegas/DEV/thebridge-advanced-gen-ai-capstone-franvillegas/backend
source venv/bin/activate
pip install pytest
```

Expected: pytest installs successfully.

- [ ] **Step 3: Create tests package**

Create `backend/tests/__init__.py` (empty file) so pytest discovers the folder.

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt backend/tests/__init__.py
git commit -m "chore: add pytest to backend"
```

---

### Task 2: Create prompt files and loader

**Files:**
- Create: `backend/agent_graph/prompts/supervisor.md`
- Create: `backend/agent_graph/prompts/tasks_agent.md`
- Create: `backend/agent_graph/prompts/calendar_agent.md`
- Create: `backend/agent_graph/prompts/chat.md`
- Create: `backend/agent_graph/prompts.py`
- Modify: `backend/agent_graph/supervisor.py`
- Modify: `backend/agent_graph/tasks_agent.py`
- Modify: `backend/agent_graph/calendar_agent.py`
- Modify: `backend/agent_graph/graph.py`

- [ ] **Step 1: Create prompt directory and files**

Create `backend/agent_graph/prompts/supervisor.md`:

```markdown
You are a supervisor agent for a task and calendar management system.
Route the user's message to the most appropriate specialist agent:

- tasks_agent: For daily tasks, todo lists, task management
- calendar_agent: For deadlines, milestones, dates, calendar events
- chat: For general conversation, greetings, help

Respond with ONLY the agent name: tasks_agent, calendar_agent, or chat
```

Create `backend/agent_graph/prompts/tasks_agent.md`:

```markdown
You are a task management specialist. You help users create, list, update and delete local tasks stored in SQLite.

Available tools:
- create_task(title, description="", priority="medium", due_date="", project_id=0)
- list_tasks(status="", project_id=0)
- update_task(task_id, status="", priority="", title="", description="", due_date="")
- delete_task(task_id)

Rules:
- If the user wants to create a task and the title is missing, ask for the title explicitly. Do not guess it.
- Do not invent optional values like project_id, priority or due_date. Only use values the user provides.
- After creating, updating or deleting a task, briefly summarize what you did in Spanish.
- Use ISO date format YYYY-MM-DD for due_date.
```

Create `backend/agent_graph/prompts/calendar_agent.md`:

```markdown
You are a calendar specialist. You help users view and add calendar events, deadlines and milestones.

Available tools:
- get_calendar_events(start_date="", end_date="", project_id=0)
- get_upcoming_deadlines(days=7)
- add_calendar_event(title, event_date, event_type="deadline", start_time="09:00", end_time="09:30", project_id=0, allow_overlap=false)
- check_calendar_overlap(event_date, start_time, end_time)

Rules:
- If the user wants to create an event and the title or date is missing, ask for the missing information explicitly.
- If the user provides a start/end time, always call check_calendar_overlap before add_calendar_event.
- If check_calendar_overlap finds conflicts, list them and ask the user: "Se solapa con: [events]. ¿Quieres cambiar la hora o dejarlo a la hora propuesta?"
- If the user chooses to keep the proposed time, call add_calendar_event with allow_overlap=true.
- If the user provides a different time, call check_calendar_overlap again with the new time.
- Use ISO date format YYYY-MM-DD for event_date and HH:MM for times.
```

Create `backend/agent_graph/prompts/chat.md`:

```markdown
You are a helpful AI assistant for an Agile project management system.
Answer the user's question conversationally. Be concise and friendly.
```

- [ ] **Step 2: Create prompt loader**

Create `backend/agent_graph/prompts.py`:

```python
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
```

- [ ] **Step 3: Refactor agents to use loaded prompts**

Modify `backend/agent_graph/supervisor.py`: replace the inline `SUPERVISOR_PROMPT` string with:

```python
from .prompts import SUPERVISOR_PROMPT
```

Remove the old `SUPERVISOR_PROMPT = """..."""` block.

Modify `backend/agent_graph/tasks_agent.py`: replace the inline `TASKS_AGENT_PROMPT` string with:

```python
from .prompts import TASKS_AGENT_PROMPT
```

Remove the old `TASKS_AGENT_PROMPT = """..."""` block.

Modify `backend/agent_graph/calendar_agent.py`: replace the inline `CALENDAR_AGENT_PROMPT` string with:

```python
from .prompts import CALENDAR_AGENT_PROMPT
```

Remove the old `CALENDAR_AGENT_PROMPT = """..."""` block.

Modify `backend/agent_graph/graph.py`: replace the inline `CHAT_PROMPT` string with:

```python
from .prompts import CHAT_PROMPT
```

Remove the old `CHAT_PROMPT = """..."""` block.

- [ ] **Step 4: Run a smoke test**

Run from the repository root:

```bash
cd /Users/franvillegas/DEV/thebridge-advanced-gen-ai-capstone-franvillegas
source backend/venv/bin/activate
python -c "from backend.agent_graph.prompts import SUPERVISOR_PROMPT, TASKS_AGENT_PROMPT, CALENDAR_AGENT_PROMPT, CHAT_PROMPT; print('supervisor:', SUPERVISOR_PROMPT[:30]); print('tasks:', TASKS_AGENT_PROMPT[:30]); print('calendar:', CALENDAR_AGENT_PROMPT[:30]); print('chat:', CHAT_PROMPT[:30])"
```

Expected: each prompt prints its first 30 characters without errors.

- [ ] **Step 5: Commit**

```bash
git add backend/agent_graph/prompts/ backend/agent_graph/prompts.py backend/agent_graph/supervisor.py backend/agent_graph/tasks_agent.py backend/agent_graph/calendar_agent.py backend/agent_graph/graph.py
git commit -m "refactor: move agent prompts to dedicated prompts folder"
```

---

### Task 3: Add calendar overlap detection

**Files:**
- Modify: `backend/tools/calendar_tools.py`
- Create: `backend/tests/test_calendar_overlap.py`

- [ ] **Step 1: Extract overlap logic to a pure helper**

At the top of `backend/tools/calendar_tools.py`, add:

```python
def _time_to_minutes(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m


def _intervals_overlap(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    """Return True if two [start, end) intervals overlap."""
    a_start = _time_to_minutes(start_a)
    a_end = _time_to_minutes(end_a)
    b_start = _time_to_minutes(start_b)
    b_end = _time_to_minutes(end_b)
    return a_start < b_end and a_end > b_start
```

- [ ] **Step 2: Add check_calendar_overlap tool**

Add this tool to `backend/tools/calendar_tools.py`:

```python
@tool
def check_calendar_overlap(event_date: str, start_time: str, end_time: str) -> str:
    """Check whether a proposed calendar event overlaps with existing events on the same date."""
    logger.info("Tool check_calendar_overlap called — date=%s, start=%s, end=%s",
                event_date, start_time, end_time)
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM calendar_events WHERE event_date = ? ORDER BY start_time ASC",
            (event_date,),
        ).fetchall()
        conflicts = []
        for row in rows:
            if _intervals_overlap(start_time, end_time, row["start_time"], row["end_time"]):
                conflicts.append(
                    f"- {row['title']} ({row['start_time']} - {row['end_time']})"
                )
        if not conflicts:
            logger.info("check_calendar_overlap: no conflicts")
            return "No overlaps found."
        logger.info("check_calendar_overlap: %d conflicts", len(conflicts))
        return "Overlap detected with existing events:\n" + "\n".join(conflicts)
    finally:
        conn.close()
```

- [ ] **Step 3: Update add_calendar_event signature and overlap behavior**

Replace the existing `add_calendar_event` function with:

```python
@tool
def add_calendar_event(
    title: str,
    event_date: str,
    event_type: str = "deadline",
    start_time: str = "09:00",
    end_time: str = "09:30",
    project_id: int = 0,
    allow_overlap: bool = False,
) -> str:
    """Add a calendar event. event_type: deadline, milestone, sprint_start, sprint_end."""
    logger.info("Tool add_calendar_event called — title=%s, date=%s, type=%s, time=%s-%s, project=%s, allow_overlap=%s",
                title[:100], event_date, event_type, start_time, end_time, project_id or "none", allow_overlap)
    conn = get_db()
    try:
        if not allow_overlap:
            conflicts = []
            rows = conn.execute(
                "SELECT * FROM calendar_events WHERE event_date = ?",
                (event_date,),
            ).fetchall()
            for row in rows:
                if _intervals_overlap(start_time, end_time, row["start_time"], row["end_time"]):
                    conflicts.append(
                        f"{row['title']} ({row['start_time']} - {row['end_time']})"
                    )
            if conflicts:
                logger.info("add_calendar_event: overlap blocked for '%s' on %s", title, event_date)
                return (
                    f"Cannot add '{title}' because it overlaps with: "
                    + ", ".join(conflicts)
                    + ". If you want to add it anyway, set allow_overlap=true."
                )
        conn.execute(
            "INSERT INTO calendar_events (title, event_date, start_time, end_time, event_type, project_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, event_date, start_time, end_time, event_type, project_id or None),
        )
        conn.commit()
        logger.info("add_calendar_event: event '%s' added on %s %s-%s", title, event_date, start_time, end_time)
        return f"Calendar event '{title}' added on {event_date} from {start_time} to {end_time}."
    finally:
        conn.close()
```

- [ ] **Step 4: Export the new tool**

Update the `calendar_tools` list at the bottom of the file:

```python
calendar_tools = [get_calendar_events, get_upcoming_deadlines, add_calendar_event, check_calendar_overlap]
```

- [ ] **Step 5: Write tests for overlap logic**

Create `backend/tests/test_calendar_overlap.py`:

```python
from backend.tools.calendar_tools import _intervals_overlap


def test_non_overlapping_intervals():
    assert _intervals_overlap("09:00", "10:00", "10:00", "11:00") is False
    assert _intervals_overlap("10:00", "11:00", "09:00", "10:00") is False


def test_overlapping_intervals():
    assert _intervals_overlap("09:00", "10:30", "10:00", "11:00") is True
    assert _intervals_overlap("10:00", "11:00", "09:00", "10:30") is True


def test_nested_intervals():
    assert _intervals_overlap("09:00", "12:00", "10:00", "11:00") is True
```

- [ ] **Step 6: Run tests**

Run:

```bash
cd /Users/franvillegas/DEV/thebridge-advanced-gen-ai-capstone-franvillegas/backend
source venv/bin/activate
pytest backend/tests/test_calendar_overlap.py -v
```

Expected: 3 tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/tools/calendar_tools.py backend/tests/test_calendar_overlap.py
git commit -m "feat: detect calendar event overlaps before creation"
```

---

### Task 4: Build structured response helper

**Files:**
- Modify: `backend/agent_graph/utils.py`
- Create: `backend/tests/test_response_builder.py`

- [ ] **Step 1: Add DB helpers to utils.py**

Append to `backend/agent_graph/utils.py`:

```python
import os
import re
import sqlite3
from typing import Any, Optional


def _get_db():
    db_path = os.getenv("DATABASE_URL", "frontend/drizzle/data.db")
    if db_path.startswith("file:"):
        db_path = db_path[5:]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_task_id(message: str) -> Optional[int]:
    match = re.search(r"Task created with id (\d+)", message)
    return int(match.group(1)) if match else None


def _parse_event_info(message: str) -> Optional[tuple[str, str]]:
    match = re.search(r"Calendar event '([^']+)' added on ([\d\-]+)", message)
    return (match.group(1), match.group(2)) if match else None


def build_created_entity(tool_name: str, tool_result: str) -> Optional[dict[str, Any]]:
    if tool_name == "create_task":
        task_id = _parse_task_id(tool_result)
        if task_id is None:
            return None
        conn = _get_db()
        try:
            row = conn.execute("SELECT * FROM local_tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                return None
            return {
                "type": "task",
                "data": {
                    "id": row["id"],
                    "title": row["title"],
                    "status": row["status"],
                    "priority": row["priority"],
                    "due_date": row["due_date"],
                    "project_id": row["project_id"],
                },
            }
        finally:
            conn.close()

    if tool_name == "add_calendar_event":
        info = _parse_event_info(tool_result)
        if info is None:
            return None
        title, event_date = info
        conn = _get_db()
        try:
            row = conn.execute(
                "SELECT * FROM calendar_events WHERE title = ? AND event_date = ? ORDER BY id DESC LIMIT 1",
                (title, event_date),
            ).fetchone()
            if not row:
                return None
            return {
                "type": "calendar_event",
                "data": {
                    "id": row["id"],
                    "title": row["title"],
                    "event_date": row["event_date"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "event_type": row["event_type"],
                    "project_id": row["project_id"],
                },
            }
        finally:
            conn.close()

    return None


def get_refresh_targets(tool_name: str) -> list[str]:
    if tool_name in {"create_task", "update_task", "delete_task"}:
        return ["tasks", "dashboard"]
    if tool_name == "add_calendar_event":
        return ["calendar", "dashboard"]
    return []
```

- [ ] **Step 2: Write tests for parse helpers**

Create `backend/tests/test_response_builder.py`:

```python
from backend.agent_graph.utils import _parse_task_id, _parse_event_info


def test_parse_task_id():
    assert _parse_task_id("Task created with id 42") == 42
    assert _parse_task_id("No id here") is None


def test_parse_event_info():
    assert _parse_event_info("Calendar event 'Sprint planning' added on 2026-06-17.") == ("Sprint planning", "2026-06-17")
    assert _parse_event_info("No event here") is None
```

- [ ] **Step 3: Run tests**

Run:

```bash
cd /Users/franvillegas/DEV/thebridge-advanced-gen-ai-capstone-franvillegas/backend
source venv/bin/activate
pytest backend/tests/test_response_builder.py -v
```

Expected: 2 tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend/agent_graph/utils.py backend/tests/test_response_builder.py
git commit -m "feat: add helper to build structured chat response from tool results"
```

---

### Task 5: Update run_graph.py to return structured JSON

**Files:**
- Modify: `backend/run_graph.py`

- [ ] **Step 1: Import helpers**

At the top of `backend/run_graph.py`, add:

```python
from backend.agent_graph.utils import build_created_entity, get_refresh_targets
```

- [ ] **Step 2: Find the last tool result**

In `main()`, after `result = graph.invoke(state)`, add:

```python
    last_tool_name = None
    last_tool_result = None
    for msg in reversed(result["messages"]):
        if getattr(msg, "type", None) == "tool":
            last_tool_name = getattr(msg, "name", None)
            last_tool_result = getattr(msg, "content", None)
            break
```

- [ ] **Step 3: Build the structured response**

Replace the existing `output = extract_text(last_msg.content)` block with:

```python
    output = extract_text(last_msg.content)

    created_entity = None
    refresh = []
    if last_tool_name and isinstance(last_tool_result, str):
        created_entity = build_created_entity(last_tool_name, last_tool_result)
        refresh = get_refresh_targets(last_tool_name)

    final_agent = result.get("current_agent", "unknown")
    response_payload = {
        "content": output,
        "agent": final_agent,
        "created_entity": created_entity,
        "refresh": refresh,
    }

    logger.info(
        "Graph completed — session_id=%s, final_agent=%s, output_length=%d, created_entity=%s, refresh=%s",
        session_id or "n/a",
        final_agent,
        len(output),
        created_entity is not None,
        refresh,
    )
    logger.debug("Assistant output: %s", output[:500])
    print(json.dumps(response_payload), flush=True)
```

Remove the old `print(json.dumps({"content": output, "agent": final_agent}), flush=True)` line.

- [ ] **Step 4: Commit**

```bash
git add backend/run_graph.py
git commit -m "feat: return structured chat response with created_entity and refresh targets"
```

---

### Task 6: Add frontend refresh event emitter

**Files:**
- Create: `frontend/lib/events.ts`

- [ ] **Step 1: Create the pubsub module**

Create `frontend/lib/events.ts`:

```typescript
export type RefreshTarget = "tasks" | "calendar" | "dashboard"

const listeners = new Map<RefreshTarget, Set<() => void>>()

export function onRefresh(target: RefreshTarget, callback: () => void): () => void {
  if (!listeners.has(target)) {
    listeners.set(target, new Set())
  }
  listeners.get(target)!.add(callback)
  return () => {
    listeners.get(target)?.delete(callback)
  }
}

export function emitRefresh(target: RefreshTarget): void {
  listeners.get(target)?.forEach((callback) => callback())
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/lib/events.ts
git commit -m "feat: add lightweight refresh event emitter for frontend views"
```

---

### Task 7: Update ChatContext to parse structured response and emit refreshes

**Files:**
- Modify: `frontend/components/chat/ChatContext.tsx`

- [ ] **Step 1: Import emitRefresh**

Add at the top:

```typescript
import { emitRefresh, type RefreshTarget } from "@/lib/events"
```

- [ ] **Step 2: Extend Message type**

Add `createdEntity` to the `Message` interface:

```typescript
export interface Message {
  role: "user" | "assistant"
  content: string
  agent?: string
  error?: boolean
  createdEntity?: { type: "task" | "calendar_event"; data: unknown }
}
```

- [ ] **Step 3: Define response type**

Add near the top of the file:

```typescript
interface ChatResponse {
  content: string
  agent: string
  created_entity?: { type: "task" | "calendar_event"; data: unknown }
  refresh?: RefreshTarget[]
}
```

- [ ] **Step 4: Parse the structured response**

In `sendMessage`, after the stream loop, replace the success branch (`else { setMessages(...) }`) with:

```typescript
      } else {
        let responsePayload: ChatResponse | null = null
        try {
          responsePayload = JSON.parse(streamingRef.current) as ChatResponse
        } catch {
          // Fallback: treat the whole stream as plain text content.
          responsePayload = {
            content: streamingRef.current,
            agent: activeAgentRef.current || "chat",
          }
        }

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: responsePayload.content,
            agent: responsePayload.agent,
            createdEntity: responsePayload.created_entity,
          },
        ])

        if (responsePayload.refresh) {
          responsePayload.refresh.forEach((target) => emitRefresh(target))
        }
      }
```

- [ ] **Step 5: Commit**

```bash
git add frontend/components/chat/ChatContext.tsx
git commit -m "feat: parse structured chat response and emit view refresh events"
```

---

### Task 8: Render confirmation card in chat messages

**Files:**
- Create: `frontend/components/chat/CreatedEntityCard.tsx`
- Modify: `frontend/components/chat/ChatMessage.tsx`

- [ ] **Step 1: Create CreatedEntityCard component**

Create `frontend/components/chat/CreatedEntityCard.tsx`:

```typescript
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface CreatedEntityCardProps {
  entity: { type: "task" | "calendar_event"; data: any }
}

export function CreatedEntityCard({ entity }: CreatedEntityCardProps) {
  if (entity.type === "task") {
    return (
      <Card className="mt-2 p-3 bg-muted/30 border-border/40">
        <div className="font-medium text-sm">{entity.data.title}</div>
        <div className="flex flex-wrap items-center gap-2 mt-1.5">
          <Badge variant="secondary" className="text-[10px]">
            {entity.data.status}
          </Badge>
          <Badge variant="secondary" className="text-[10px]">
            {entity.data.priority}
          </Badge>
          {entity.data.due_date && (
            <span className="text-[10px] text-muted-foreground">
              Due {entity.data.due_date}
            </span>
          )}
        </div>
      </Card>
    )
  }

  if (entity.type === "calendar_event") {
    return (
      <Card className="mt-2 p-3 bg-muted/30 border-border/40">
        <div className="font-medium text-sm">{entity.data.title}</div>
        <div className="text-[10px] text-muted-foreground mt-1">
          {entity.data.event_date} · {entity.data.start_time} - {entity.data.end_time}
        </div>
        <Badge variant="secondary" className="mt-1.5 text-[10px]">
          {entity.data.event_type}
        </Badge>
      </Card>
    )
  }

  return null
}
```

- [ ] **Step 2: Update ChatMessage to show the card**

Modify `frontend/components/chat/ChatMessage.tsx`:

Add import:

```typescript
import { CreatedEntityCard } from "./CreatedEntityCard"
```

Update interface:

```typescript
interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
  agent?: string
  error?: boolean
  createdEntity?: { type: "task" | "calendar_event"; data: any }
}
```

Update function signature:

```typescript
export function ChatMessage({ role, content, agent, error, createdEntity }: ChatMessageProps) {
```

Add the card inside the assistant message container, after the `<p>`:

```typescript
            <p className="whitespace-pre-wrap">{content}</p>
            {createdEntity && <CreatedEntityCard entity={createdEntity} />}
```

- [ ] **Step 3: Pass createdEntity in ChatPanel**

Modify `frontend/components/chat/ChatPanel.tsx`: pass `createdEntity={msg.createdEntity}` to `ChatMessage`:

```typescript
            <ChatMessage
              key={i}
              role={msg.role}
              content={msg.content}
              agent={msg.agent}
              error={msg.error}
              createdEntity={msg.createdEntity}
            />
```

- [ ] **Step 4: Commit**

```bash
git add frontend/components/chat/CreatedEntityCard.tsx frontend/components/chat/ChatMessage.tsx frontend/components/chat/ChatPanel.tsx
git commit -m "feat: render confirmation card for created tasks and calendar events"
```

---

### Task 9: Subscribe views to refresh events

**Files:**
- Modify: `frontend/components/dashboard/DashboardHome.tsx`
- Modify: `frontend/components/tasks/TaskList.tsx`
- Modify: `frontend/components/calendar/CalendarView.tsx`

- [ ] **Step 1: Update DashboardHome**

Update imports to include `useCallback` and `onRefresh`:

```typescript
import { useState, useEffect, useCallback } from "react"
import { onRefresh } from "@/lib/events"
```

Wrap the fetch logic in a `loadData` function and use `useEffect` to subscribe:

```typescript
  const loadData = useCallback(() => {
    setLoading(true)
    Promise.all([
      fetch("/api/tasks").then((r) => r.json()),
      fetch("/api/calendar").then((r) => r.json()),
    ])
      .then(([tasksData, eventsData]) => {
        setTasks(tasksData)
        setEvents(eventsData)
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  useEffect(() => {
    const unsubTasks = onRefresh("tasks", loadData)
    const unsubCalendar = onRefresh("calendar", loadData)
    const unsubDashboard = onRefresh("dashboard", loadData)
    return () => {
      unsubTasks()
      unsubCalendar()
      unsubDashboard()
    }
  }, [loadData])
```

- [ ] **Step 2: Update TaskList**

Update imports to include `useCallback` and `onRefresh`:

```typescript
import { useState, useEffect, useCallback } from "react"
import { onRefresh } from "@/lib/events"
```

Replace the `useEffect` block with:

```typescript
  const loadTasks = useCallback(() => {
    setLoading(true)
    fetch("/api/tasks")
      .then((res) => res.json())
      .then((data) => setTasks(data.tasks))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  useEffect(() => {
    return onRefresh("tasks", loadTasks)
  }, [loadTasks])
```

- [ ] **Step 3: Update CalendarView**

Update imports to include `useCallback` and `onRefresh`:

```typescript
import { useState, useEffect, useCallback } from "react"
import { onRefresh } from "@/lib/events"
```

Replace the `useEffect` block with:

```typescript
  const loadEvents = useCallback(() => {
    setLoading(true)
    fetch("/api/calendar")
      .then((res) => res.json())
      .then((data) => setEvents(data.events))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    loadEvents()
  }, [loadEvents])

  useEffect(() => {
    return onRefresh("calendar", loadEvents)
  }, [loadEvents])
```

- [ ] **Step 4: Commit**

```bash
git add frontend/components/dashboard/DashboardHome.tsx frontend/components/tasks/TaskList.tsx frontend/components/calendar/CalendarView.tsx
git commit -m "feat: refresh dashboard, tasks and calendar views on chat mutations"
```

---

### Task 10: Verification and manual end-to-end check

- [ ] **Step 1: Run backend tests**

Run:

```bash
cd /Users/franvillegas/DEV/thebridge-advanced-gen-ai-capstone-franvillegas/backend
source venv/bin/activate
pytest backend/tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Run frontend type check**

Run:

```bash
cd /Users/franvillegas/DEV/thebridge-advanced-gen-ai-capstone-franvillegas/frontend
npx tsc --noEmit
```

Expected: no TypeScript errors.

- [ ] **Step 3: Run frontend lint**

Run:

```bash
cd /Users/franvillegas/DEV/thebridge-advanced-gen-ai-capstone-franvillegas/frontend
npm run lint
```

Expected: lint passes (or only pre-existing issues).

- [ ] **Step 4: Manual end-to-end check**

Start the development servers:

```bash
# Terminal 1
cd /Users/franvillegas/DEV/thebridge-advanced-gen-ai-capstone-franvillegas/frontend
npm run dev

# Terminal 2 — the backend runs as a subprocess, no need to start separately
```

Open http://localhost:3000 and run through:

1. Create a task via chat without a title → agent asks for the title.
2. Provide the title → task is created and a confirmation card appears; dashboard pending tasks count updates.
3. Navigate to /tasks → the new task is visible without reload.
4. Create a calendar event at 10:00-11:00.
5. Create another calendar event at 10:30-11:30 on the same date → agent warns about the overlap and asks whether to change the time or keep it.
6. Answer "dejarlo a la hora propuesta" → event is created; dashboard and /calendar update.
7. Refresh the page → data persists.

- [ ] **Step 5: Commit any final fixes**

If any changes were needed during verification:

```bash
git add -A
git commit -m "fix: address verification findings"
```

---

## Spec coverage check

| Spec requirement | Task(s) |
|---|---|
| Prompts in dedicated folder | Task 2 |
| Prompts optimized (ask for missing info, etc.) | Task 2 |
| Chat returns structured response | Tasks 4, 5, 7 |
| Confirmation card for created entity | Task 8 |
| Views refresh without reload | Tasks 6, 9 |
| Calendar overlap detection | Task 3 |
| Calendar agent asks user on overlap | Task 2 (calendar prompt) + Task 3 |

## Placeholder scan

No TBD/TODO/fill-in details found. Each step includes exact file paths, code and commands.
