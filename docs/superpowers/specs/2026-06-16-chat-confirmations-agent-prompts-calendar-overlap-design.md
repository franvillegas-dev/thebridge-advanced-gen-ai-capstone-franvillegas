# Chat confirmations, agent prompts refactor and calendar overlap detection

## Context and goal

The current chat returns plain text and the agents embed their prompts as Python strings. The user wants:

1. When a task or calendar event is created/updated/deleted, the chat shows a confirmation card with the entity details.
2. Dashboard, tasks and calendar views refresh automatically without reloading the page.
3. Agent prompts live in a dedicated folder and are optimized.
4. Agents ask the user for missing information and the interface supports a free-form answer flow.
5. The calendar agent warns when a new event overlaps with an existing one and asks whether to change the time or keep the proposed time.

## Design decisions

- **No interactive graph state machine.** The user chose free-form conversational mode, so we rely on optimized prompts and conversation history instead of pausing the LangGraph execution.
- **No new data-fetching library.** React Query is already installed but we will keep the current `fetch` + `useEffect` pattern and add a lightweight event emitter to trigger refreshes, matching the existing minimal style.
- **Structured chat response.** `run_graph.py` returns a JSON object with `content`, `agent`, `created_entity` and `refresh`. The frontend renders a card when `created_entity` is present and emits refresh events for the listed targets.
- **Overlap detection as a separate tool.** A new `check_calendar_overlap` tool lets the calendar agent inspect conflicts before calling `add_calendar_event`.

## Prompt folder structure

Create `backend/agent_graph/prompts/` with one Markdown file per agent:

```
backend/agent_graph/prompts/
├── supervisor.md
├── tasks_agent.md
├── calendar_agent.md
└── chat.md
```

The Python modules load the files at import time using a path relative to `__file__`. Prompts are plain strings, no Jinja/templating for now.

### Prompt contents

**supervisor.md**

- Role: router.
- Valid outputs: `tasks_agent`, `calendar_agent`, `chat`.
- Keep it concise. No changes to the routing logic.

**tasks_agent.md**

- Role: task management specialist.
- Tools available: `create_task`, `list_tasks`, `update_task`, `delete_task`.
- Rules:
  - If the user wants to create a task and the title is missing, ask for it explicitly.
  - Do not invent optional values such as `project_id`, `priority` or `due_date`.
  - After creating, updating or deleting a task, summarize the action briefly in the response text.

**calendar_agent.md**

- Role: calendar specialist.
- Tools available: `get_calendar_events`, `get_upcoming_deadlines`, `add_calendar_event`, `check_calendar_overlap`.
- Rules:
  - If the user wants to create an event and the title or date is missing, ask for it explicitly.
  - If the user provides a time, always call `check_calendar_overlap` before `add_calendar_event`.
  - If overlaps exist, list the conflicting events and ask the user whether to change the time or keep the proposed time.
  - If the user says to keep the proposed time, call `add_calendar_event` with `allow_overlap=true`.
  - If the user provides a new time, call `check_calendar_overlap` again.

**chat.md**

- Role: helpful general assistant.
- Keep answers concise and friendly.

## Backend response format

`run_graph.py` prints a single JSON line:

```json
{
  "content": "He creado la tarea de diseño.",
  "agent": "tasks_agent",
  "created_entity": {
    "type": "task",
    "data": {
      "id": 12,
      "title": "Diseño de mockups",
      "status": "pending",
      "priority": "high",
      "due_date": "2026-06-17",
      "project_id": null
    }
  },
  "refresh": ["tasks", "dashboard"]
}
```

Fields:

- `content` (string, required): natural language response.
- `agent` (string, required): final agent name.
- `created_entity` (object | null): present when a task or calendar event was created/updated/deleted.
  - `type`: `"task"` or `"calendar_event"`.
  - `data`: the entity fields, matching the frontend types.
- `refresh` (string[]): list of views to refresh. Values: `"tasks"`, `"calendar"`, `"dashboard"`.

The `created_entity` object is built deterministically from the last tool result when possible, without an extra LLM call. If building it fails, the field is omitted and the response falls back to plain text.

## Confirmation card in the chat

`ChatMessage` receives an optional `createdEntity` prop. When present, it renders a small card below the text message:

- Task card: title, status badge, priority badge, due date.
- Calendar event card: title, date, start/end time, event type badge.

The card reuses existing UI primitives (`Card`, `Badge`) and follows the glassmorphism style already in the project.

## Calendar overlap detection

### New tool: `check_calendar_overlap`

```python
@tool
def check_calendar_overlap(event_date: str, start_time: str, end_time: str) -> str:
    ...
```

- Query `calendar_events` for rows where `event_date = event_date` and the intervals `[start_time, end_time]` overlap.
- Return a readable list of conflicts or `"No overlaps found."`.

### Updated tool: `add_calendar_event`

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
    ...
```

- If `allow_overlap=false`, the tool checks for overlaps before inserting. If any exist, it returns an error message with the conflicts and does not insert.
- If `allow_overlap=true`, it inserts directly.
- Insert includes `start_time` and `end_time` using the schema defaults when not provided.

### Agent flow

1. User requests a new calendar event.
2. Agent calls `check_calendar_overlap` with the proposed date/time.
3. If conflicts:
   - Agent lists them in the chat and asks: *“Se solapa con: X. ¿Quieres cambiar la hora o dejarlo a la hora propuesta?”*
4. User answers.
   - If answer is "dejarlo" / "a la misma hora": agent calls `add_calendar_event(..., allow_overlap=true)`.
   - If answer provides a new time: agent repeats step 2.

## View refresh mechanism

Create a lightweight pubsub module `frontend/lib/events.ts`:

```ts
export type RefreshTarget = "tasks" | "calendar" | "dashboard";

export function onRefresh(target: RefreshTarget, callback: () => void): () => void;
export function emitRefresh(target: RefreshTarget): void;
```

Implementation uses a module-level `Map<RefreshTarget, Set<() => void>>`.

### Subscribers

- `DashboardHome` subscribes to `"tasks"` and `"calendar"` and refetches both.
- `TaskList` subscribes to `"tasks"` and refetches `/api/tasks`.
- `CalendarView` subscribes to `"calendar"` and refetches `/api/calendar`.

Each component registers its refresh callback in a `useEffect` and unsubscribes on unmount.

### Emitter

`ChatContext`, after appending the assistant message to the conversation, iterates over `response.refresh` and calls `emitRefresh(target)` for each entry.

## Clarifying questions flow

Because the user chose free-form mode, no UI blocking or special graph state is required. The optimized prompts instruct the agents to:

- Ask for missing required fields before acting.
- Avoid hallucinating optional fields.

The existing `previous_messages` mechanism preserves the question/answer pair, so the agent continues naturally on the next user message.

## Error handling and edge cases

- Database errors in tools return a clear message; the agent forwards it to the user.
- If `check_calendar_overlap` fails, the agent reports the failure and may still proceed if the user explicitly asks to keep the time.
- If `created_entity` cannot be built, the response is shown as plain text without a card.
- If a refresh fetch fails, the affected component shows a local error and does not break the chat.
- Invalid date/time formats are rejected by the tools with a helpful message.

## Files to change

- New:
  - `backend/agent_graph/prompts/*.md`
  - `backend/agent_graph/prompts.py` (loader)
  - `frontend/lib/events.ts`
  - `frontend/components/chat/CreatedEntityCard.tsx` (or inline in ChatMessage)
- Modify:
  - `backend/agent_graph/supervisor.py`
  - `backend/agent_graph/tasks_agent.py`
  - `backend/agent_graph/calendar_agent.py`
  - `backend/agent_graph/graph.py`
  - `backend/agent_graph/utils.py` (helper to build created_entity)
  - `backend/tools/calendar_tools.py`
  - `backend/run_graph.py`
  - `frontend/app/api/chat/route.ts`
  - `frontend/components/chat/ChatContext.tsx`
  - `frontend/components/chat/ChatMessage.tsx`
  - `frontend/components/dashboard/DashboardHome.tsx`
  - `frontend/components/tasks/TaskList.tsx`
  - `frontend/components/calendar/CalendarView.tsx`

## Out of scope

- Persistent session state for paused graphs.
- React Query migration for data fetching.
- Editing events through the chat.
- Real-time collaboration or websockets.

## Success criteria

- Creating a task via chat renders a confirmation card and updates the dashboard/task list without reload.
- Creating a calendar event via chat renders a confirmation card and updates the dashboard/calendar view without reload.
- Prompts are loaded from `backend/agent_graph/prompts/`.
- Asking to create a task without a title makes the agent ask for the title.
- Creating a calendar event at a time that overlaps with an existing one shows the conflict and asks the user; keeping the time creates the event anyway.
