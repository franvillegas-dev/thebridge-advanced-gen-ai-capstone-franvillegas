# Dashboard Homepage & Persistent Chat Panel

## Objective

1. Convert `/` (home) into a dashboard showing KPIs, today's tasks, and today's events.
2. Move the AI chat assistant to a persistent right-side panel visible across all pages.
3. Add structured error handling: chat errors appear in conversation, config errors appear as toasts.

## Layout Structure

```
┌──────────────────────────────────────────────────────┐
│  Desktop (≥768px):                                   │
│  ┌──────┬──────────────────────────┬──────────────┐  │
│  │ Nav  │  Main Content            │  Chat Panel  │  │
│  │(56px)│  (flex-1)                │  (~400px)    │  │
│  │      │                          │              │  │
│  │ Chat │  Dashboard / Tasks /     │  Messages    │  │
│  │ Tasks│  Calendar / etc.         │  Input       │  │
│  │ Cal  │                          │              │  │
│  │ Dash │                          │  Collapse ▲  │  │
│  └──────┴──────────────────────────┴──────────────┘  │
│                                                      │
│  Mobile (<768px):                                    │
│  ┌──────────────────────────────┐                   │
│  │  Main Content (full width)   │                   │
│  │                              │                   │
│  │  ┌────────────────────────┐ │                   │
│  │  │ Chat opens as slide-up │ │                   │
│  │  │ drawer (80vh)          │ │                   │
│  │  └────────────────────────┘ │                   │
│  └──────────────────────────────┘                   │
└──────────────────────────────────────────────────────┘
```

## Component Architecture

### New/Modified Files

| File | Change |
|---|---|
| `frontend/app/layout.tsx` | 3-column grid: sidebar, main, chat panel. Wrap with `ChatProvider`. |
| `frontend/app/page.tsx` | Replace chat with `DashboardHome` component. |
| `frontend/app/dashboard/page.tsx` | Keep as standalone page (redirect from `/dashboard` or show same). |
| `frontend/components/dashboard/DashboardHome.tsx` | **New.** KPIs + today's tasks + today's events. |
| `frontend/components/dashboard/TodayTasks.tsx` | **New.** Filtered list of today's tasks. |
| `frontend/components/dashboard/TodayEvents.tsx` | **New.** Filtered list of today's events. |
| `frontend/components/chat/ChatPanel.tsx` | **New.** Chat wrapper with collapse toggle, fixed to right side. |
| `frontend/components/chat/ChatStream.tsx` | Refactor: accept `onError` callback for toast errors. |
| `frontend/components/chat/ChatContext.tsx` | **New.** React Context for chat state (messages, streaming, session). |
| `frontend/components/ui/toast.tsx` | **New.** Toast component + provider. |
| `frontend/app/api/chat/route.ts` | Add config validation endpoint + structured error responses. |
| `backend/agent_graph/jira_agent.py` | Wrap OpenAI/Jira calls in try/except, return error string. |
| `backend/agent_graph/story_agent.py` | Same. |
| `backend/agent_graph/tasks_agent.py` | Same. |
| `backend/agent_graph/calendar_agent.py` | Same. |
| `backend/agent_graph/supervisor.py` | Wrap OpenAI call in try/except. |
| `backend/tools/jira_tools.py` | Wrap async calls, return error string on failure. |
| `backend/mcp/jira_mcp_client.py` | Add try/except around all HTTP calls, return dict with `error` key. |

### ChatContext (React Context)

```typescript
interface ChatContextValue {
  messages: Message[]
  streamingContent: string
  isLoading: boolean
  isOpen: boolean
  sendMessage: (text: string) => Promise<void>
  togglePanel: () => void
  closePanel: () => void
}
```

Placed at layout level so state survives page navigation.

### ChatPanel Component

- Fixed right panel, ~400px wide on desktop
- Collapse button at top-right of panel (or chevron)
- When collapsed: thin strip with expand button, or hidden entirely
- Mobile (<768px): hidden by default, opens as a slide-up drawer overlay (80vh)
- Chat input and messages same as current ChatStream

### DashboardHome Component

- Calls `/api/tasks` and `/api/calendar` on mount
- Filters tasks where `dueDate === today` (ISO date: `new Date().toISOString().split('T')[0]` to match SQLite date format)
- Filters events where `eventDate === today` (same format)
- Renders:
  1. **KPI row**: same 4 cards as current DashboardGrid
  2. **Today's tasks**: TaskCard list filtered to today
  3. **Today's events**: CalendarView list filtered to today
- Loading states while fetching
- Empty states when no tasks/events for today

### Error Handling

#### Chat errors → in conversation
Each agent/backend function wraps its LLM/tool calls:
```python
try:
    response = agent.invoke([system_msg] + messages)
except Exception as e:
    return {**state, "messages": state["messages"] + [
        AIMessage(content=f"Error: Could not connect to OpenAI. Check your API key in backend/.env")
    ]}
```

Jira tools catch HTTP errors:
```python
try:
    result = await client.search_issues(jql, max_results)
except Exception as e:
    return f"Error connecting to Jira: {e}. Verify JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN in backend/.env"
```

#### Config errors → toasts on app load
- Frontend calls `/api/health` or `/api/chat/config` on mount
- Backend returns config status (Jira configured? OpenAI key set?)
- If missing, show toast via shadcn toast provider

## Data Flow

```
App Load
  ├─→ GET /api/chat/config → check env vars → toast if missing
  └─→ GET /api/tasks + /api/calendar → render dashboard

User sends chat message
  └─→ POST /api/chat (SSE stream)
       └─→ spawn python3 subprocess
            └─→ LangGraph graph.invoke()
                 ├─→ supervisor (OpenAI) → agent
                 ├─→ agent (OpenAI + Jira/Local tools)
                 └─→ response streamed back via SSE

Error during chat
  └─→ Python catches exception → returns AIMessage with error text
       └─→ Frontend renders as assistant message in chat panel

Config validation
  └─→ GET /api/chat/config returns { openai: bool, jira: bool }
       └─→ Frontend shows toast per missing config
```

## Navigation Changes

- Sidebar nav keeps Chat, Tasks, Calendar, Dashboard links
- "Chat" link on desktop focuses the chat panel (scrolls to it / opens if collapsed) instead of navigating
- `/dashboard` page stays as-is at its own route (redundant with home but harmless; could redirect in future)
- On mobile, chat link opens the drawer panel

## Implementation Order

1. Toast component + provider in layout
2. ChatContext + ChatPanel in layout (right side)
3. DashboardHome (home page)
4. API config validation endpoint + toast on missing config
5. Backend error wrapping (agents + Jira client + supervisor)
6. Frontend chat error handling (show in conversation)

## Scope

- Desktop-first; mobile responsive but minimal
- No auth changes
- No DB schema changes
- Backend agent logic unchanged (only error wrapping)
