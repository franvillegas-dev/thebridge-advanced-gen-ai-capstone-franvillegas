# Jira Multi-Agent System — Design Spec

## Overview

A multi-agent system that helps Project Managers and Engineering Managers manage their Jira projects through a chat interface. The system provides a responsive web application with chat, calendar, task management, and a dashboard — with the ability to create and manage Jira items through natural language.

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | LangGraph (Python) |
| Frontend | Next.js (App Router) + TypeScript |
| UI | Tailwind CSS + shadcn/ui |
| Database | SQLite via Drizzle ORM (MVP), upgradable |
| Jira Integration | MCP (primary), REST API (fallback) |
| Chat Streaming | Server-Sent Events (SSE) |
| Auth | None (MVP), post-MVP |

## Architecture

```
Frontend (Next.js)                  Backend (Next.js API + Python)
┌─────────────────────┐            ┌──────────────────────────┐
│  Chat / Calendar /   │  HTTP+SSE  │  API Routes              │
│  Tasks / Dashboard   │◄─────────►│                          │
│                      │            │  POST /api/chat → SSE    │
│  - Responsive        │            │  GET/POST /api/tasks     │
│  - Mobile-first      │            │  GET /api/calendar       │
│  - shadcn/ui         │            │  GET /api/projects       │
└─────────────────────┘            └────────┬─────────────────┘
                                            │
                                    ┌───────┴──────────┐
                                    │ LangGraph (Python)│
                                    │                   │
                                    │   Supervisor      │
                                    │   ┌─────┬───┬──┐ │
                                    │   │Jira │Tsk│Cal│ │
                                    │   │Story│   │   │ │
                                    │   └─────┴───┴──┘ │
                                    └───────┬──────────┘
                                            │
                                    ┌───────┴──────────┐
                                    │ Jira Cloud (MCP) │
                                    └──────────────────┘
```

### Multi-Agent Architecture (LangGraph)

**Approach:** Supervisor agent with specialized sub-agents.

#### Agent State

```python
class AgentState(TypedDict):
    messages: list
    current_agent: str
    pending_publish: list
    context: dict
```

#### Agents

| Agent | Responsibility | Tools |
|---|---|---|
| **Supervisor** | Routes messages to the correct sub-agent based on intent | LLM router |
| **Jira Agent** | CRUD on Jira issues, search, sprint reports | `search_issues`, `get_issue`, `create_issue`, `update_issue`, `get_sprint_report` via MCP |
| **Tasks Agent** | Manages local daily tasks, publishes to Jira on demand | `create_task`, `list_tasks`, `update_task`, `delete_task`, `publish_to_jira` |
| **Calendar Agent** | Deadlines, milestones, sprint timelines | `get_deadlines`, `get_milestones`, `get_sprint_timeline` |
| **Story Refinement Agent** | Refines user stories, splits stories, estimates effort | `refine_story`, `split_story`, `estimate_effort` |

### Graph Flow

```
User Message → Supervisor (LLM decides intent)
                    │
                    ├──→ jira_agent → responder
                    ├──→ tasks_agent → responder
                    ├──→ calendar_agent → responder
                    └──→ story_agent → responder
                              │
                         responder → User
```

## Frontend Structure

### Pages / Routes

| Route | Component | Description |
|---|---|---|
| `/` | `ChatPage` | Chat interface with SSE streaming |
| `/calendar` | `CalendarPage` | Deadline and milestone calendar |
| `/tasks` | `TasksPage` | Today's tasks and pending items |
| `/dashboard` | `DashboardPage` | KPIs, sprint status, project overview |
| `/settings` | `SettingsPage` | Jira connection config, preferences |

### Layout

```
Mobile (single column with tabbed navigation):
┌─────────────────┐
│ Header          │
├─────────────────┤
│ Active View     │
│ (Chat/Calendar/ │
│  Tasks/Dash)    │
├─────────────────┤
│ Bottom Nav Bar  │
└─────────────────┘

Desktop (sidebar + main panel):
┌────────┬────────────────────┐
│ Sidebar│   Main Content     │
│        │                    │
│ Chat   │   Chat / Calendar  │
│ Tasks  │   / Tasks / Dashboard│
│ Cal    │                    │
│ Dash   │                    │
│        │                    │
└────────┴────────────────────┘
```

### Dashboard KPIs

- Active issues per project (from Jira)
- Today's tasks (local SQLite)
- Upcoming deadlines (next 5)
- Active sprint status (completed vs remaining, from Jira)
- Tasks pending Jira publish (synced: false)

## Data Model

### Tables

```sql
-- MVP: no auth

projects
  id          integer PRIMARY KEY
  name        text NOT NULL
  jira_key    text
  description text
  created_at  text DEFAULT (datetime('now'))

local_tasks
  id            integer PRIMARY KEY
  title         text NOT NULL
  description   text
  status        text DEFAULT 'pending'  -- pending | in_progress | done
  priority      text DEFAULT 'medium'   -- low | medium | high | critical
  due_date      text
  project_id    integer REFERENCES projects(id)
  jira_issue_id text
  synced        integer DEFAULT 0       -- 0 = local only, 1 = published to Jira
  created_at    text DEFAULT (datetime('now'))

chat_history
  id         integer PRIMARY KEY
  session_id text NOT NULL
  role       text NOT NULL              -- user | assistant
  content    text NOT NULL
  created_at text DEFAULT (datetime('now'))

calendar_events
  id         integer PRIMARY KEY
  title      text NOT NULL
  event_date text NOT NULL
  event_type text NOT NULL              -- deadline | milestone | sprint_start | sprint_end
  source     text DEFAULT 'local'       -- local | jira
  project_id integer REFERENCES projects(id)
  created_at text DEFAULT (datetime('now'))
```

### Jira Publication Flow

1. User creates task → saved as `local_task` with `synced=0`
2. User asks to publish → `publish_to_jira` tool creates issue via MCP
3. On success → `jira_issue_id` saved, `synced=1`
4. Task now linked to Jira issue

## API Design

```
POST /api/chat
  Body: { message: string, session_id?: string }
  Response: SSE stream of message tokens

GET  /api/tasks
  Query: { status?, project_id?, date? }
  Response: { tasks: Task[] }

POST /api/tasks
  Body: { title, description, priority, due_date, project_id }
  Response: { task: Task }

PATCH /api/tasks/:id
  Body: { status?, priority?, title?, description?, due_date? }
  Response: { task: Task }

DELETE /api/tasks/:id
  Response: { ok: boolean }

POST /api/tasks/:id/publish
  → Publishes local task to Jira
  Response: { jira_issue_id: string, jira_url: string }

GET  /api/calendar
  Query: { start_date?, end_date?, project_id? }
  Response: { events: CalendarEvent[] }

GET  /api/projects
  Response: { projects: Project[] }

POST /api/projects
  Body: { name, jira_key?, description? }
  Response: { project: Project }
```

## Jira Integration

### Layer 1: MCP (Primary)

LangGraph agent connects to a Jira MCP server that exposes tools. Each tool is a LangChain tool wrapped around the MCP client.

### Layer 2: REST API (Fallback)

If MCP is unavailable, use direct REST calls via `httpx` or `jira-python`.

### Configuration

```
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=user@example.com
JIRA_API_TOKEN=your_token
JIRA_MCP_SERVER=optional_mcp_server_url
```

## Testing Strategy

| Layer | Tool | Scope |
|---|---|---|
| Agents | pytest + LangGraph test utils | Unit test each agent with mocked tools, integration test the graph |
| API | Vitest + supertest | Route handlers, error handling |
| Frontend | Vitest + Testing Library | Component rendering, chat streaming |
| E2E | Playwright | Full flow: chat → create task → publish to Jira |

## Project Structure

```
agile-agent/
├── frontend/
│   ├── app/
│   │   ├── page.tsx           # Chat
│   │   ├── calendar/page.tsx
│   │   ├── tasks/page.tsx
│   │   ├── dashboard/page.tsx
│   │   ├── settings/page.tsx
│   │   └── api/
│   │       ├── chat/route.ts
│   │       ├── tasks/route.ts
│   │       ├── calendar/route.ts
│   │       └── projects/route.ts
│   ├── components/
│   │   ├── chat/
│   │   ├── calendar/
│   │   ├── tasks/
│   │   └── dashboard/
│   ├── lib/
│   │   ├── db.ts              # Drizzle client
│   │   └── agents.ts          # LangGraph subprocess bridge
│   ├── tailwind.config.ts
│   └── package.json
├── backend/
│   ├── agent_graph/
│   │   ├── __init__.py
│   │   ├── graph.py           # Main LangGraph definition
│   │   ├── supervisor.py
│   │   ├── jira_agent.py
│   │   ├── tasks_agent.py
│   │   ├── calendar_agent.py
│   │   └── story_agent.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── jira_tools.py
│   │   ├── tasks_tools.py
│   │   ├── calendar_tools.py
│   │   └── story_tools.py
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── jira_mcp_client.py
│   ├── pyproject.toml
│   └── requirements.txt
├── drizzle/
│   └── schema.ts
├── docker-compose.yml
└── README.md
```

## Future Considerations

- Voice chat (Web Speech API → transcript → LangGraph)
- Multi-user auth (NextAuth.js / Clerk)
- PostgreSQL migration
- Real-time sync with Jira webhooks
- Mobile app (PWA or React Native)
