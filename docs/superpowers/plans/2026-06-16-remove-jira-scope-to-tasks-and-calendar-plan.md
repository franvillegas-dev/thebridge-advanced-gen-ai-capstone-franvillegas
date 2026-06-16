# Remove Jira Integration and Scope to Tasks + Calendar — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all Jira integration, the Story Refinement agent, and related frontend/DB artifacts, leaving only local task management and calendar event functionality.

**Architecture:** The LangGraph workflow is reduced to a Supervisor that routes between Tasks Agent, Calendar Agent, and a chat responder. The SQLite schema keeps only `projects`, `local_tasks`, `calendar_events`, and `chat_history`. The frontend keeps chat, tasks, and calendar pages, removing Jira config checks and publish-to-Jira UI.

**Tech Stack:** Python 3, LangGraph/LangChain, Google Gemini, Next.js 16, TypeScript, SQLite via Drizzle ORM.

---

## Task 1: Delete obsolete backend files

**Files:**
- Delete: `backend/agent_graph/jira_agent.py`
- Delete: `backend/agent_graph/story_agent.py`
- Delete: `backend/mcp/jira_mcp_client.py`
- Delete: `backend/mcp/__init__.py`
- Delete: `backend/tools/jira_tools.py`
- Delete: `backend/tools/story_tools.py`

- [ ] **Step 1: Delete the files**

```bash
rm backend/agent_graph/jira_agent.py
rm backend/agent_graph/story_agent.py
rm backend/mcp/jira_mcp_client.py
rm backend/mcp/__init__.py
rm backend/tools/jira_tools.py
rm backend/tools/story_tools.py
```

- [ ] **Step 2: Remove the empty `backend/mcp/` directory**

```bash
rmdir backend/mcp 2>/dev/null || true
```

- [ ] **Step 3: Verify deletions**

```bash
git status --short
```

Expected: `D` entries for the six files above.

- [ ] **Step 4: Commit**

```bash
git add backend/agent_graph/jira_agent.py backend/agent_graph/story_agent.py backend/mcp/jira_mcp_client.py backend/mcp/__init__.py backend/tools/jira_tools.py backend/tools/story_tools.py
git commit -m "chore: remove jira agent, story agent, mcp client, and related tools"
```

---

## Task 2: Clean Jira publishing from tasks tools

**Files:**
- Modify: `backend/tools/tasks_tools.py`

- [ ] **Step 1: Remove the Jira client import**

Replace line 5:

```python
from ..mcp.jira_mcp_client import JiraMCPClient
```

with:

```python
# No external integrations
```

or simply delete it. Also remove `import asyncio` if it is no longer used elsewhere in the file.

- [ ] **Step 2: Delete the `publish_task_to_jira` function and its registration**

Delete the entire function (lines 127-156) and update the tools list at the bottom:

```python
tasks_tools = [create_task, list_tasks, update_task, delete_task]
```

- [ ] **Step 3: Verify the file content**

The remaining imports should be:

```python
import sqlite3
import os
import logging
from langchain_core.tools import tool
```

- [ ] **Step 4: Commit**

```bash
git add backend/tools/tasks_tools.py
git commit -m "chore: remove publish_task_to_jira tool"
```

---

## Task 3: Update supervisor routing

**Files:**
- Modify: `backend/agent_graph/supervisor.py`

- [ ] **Step 1: Replace the supervisor prompt**

Replace `SUPERVISOR_PROMPT` with:

```python
SUPERVISOR_PROMPT = """You are a supervisor agent for a task and calendar management system.
Route the user's message to the most appropriate specialist agent:

- tasks_agent: For daily tasks, todo lists, task management
- calendar_agent: For deadlines, milestones, dates, calendar events
- chat: For general conversation, greetings, help

Respond with ONLY the agent name: tasks_agent, calendar_agent, or chat"""
```

- [ ] **Step 2: Update valid agent sets**

In the fallback block (around line 68), replace:

```python
if agent_name in {"jira_agent", "tasks_agent", "calendar_agent", "story_agent", "chat"}:
```

with:

```python
if agent_name in {"tasks_agent", "calendar_agent", "chat"}:
```

And near line 74, replace:

```python
valid_agents = {"jira_agent", "tasks_agent", "calendar_agent", "story_agent", "chat"}
```

with:

```python
valid_agents = {"tasks_agent", "calendar_agent", "chat"}
```

- [ ] **Step 3: Commit**

```bash
git add backend/agent_graph/supervisor.py
git commit -m "chore: limit supervisor routing to tasks, calendar, and chat"
```

---

## Task 4: Update LangGraph workflow

**Files:**
- Modify: `backend/agent_graph/graph.py`

- [ ] **Step 1: Remove obsolete imports**

Delete these import lines:

```python
from .jira_agent import handle_jira
from .story_agent import handle_story
from ..tools.jira_tools import jira_tools
from ..tools.story_tools import story_tools
```

Keep:

```python
import json
import logging
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from .state import AgentState
from .supervisor import route_to_agent
from .tasks_agent import handle_tasks
from .calendar_agent import handle_calendar
from .llm import create_llm, invoke_with_retry, get_fallback_model_name, is_rate_limited
from ..tools.tasks_tools import tasks_tools
from ..tools.calendar_tools import calendar_tools
from .utils import extract_text
```

- [ ] **Step 2: Update the tools list**

Replace:

```python
all_tools = jira_tools + tasks_tools + calendar_tools + story_tools
```

with:

```python
all_tools = tasks_tools + calendar_tools
```

- [ ] **Step 3: Remove Jira/Story nodes and edges**

Delete the node additions:

```python
workflow.add_node("jira_agent", handle_jira)
workflow.add_node("story_agent", handle_story)
```

Keep:

```python
workflow.add_node("log_start", log_invocation)
workflow.add_node("supervisor", lambda state: state)
workflow.add_node("tasks_agent", handle_tasks)
workflow.add_node("calendar_agent", handle_calendar)
workflow.add_node("responder", handle_chat)
workflow.add_node("tools", logged_tool_node)
```

- [ ] **Step 4: Update supervisor conditional edges**

Replace:

```python
workflow.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {
        "jira_agent": "jira_agent",
        "tasks_agent": "tasks_agent",
        "calendar_agent": "calendar_agent",
        "story_agent": "story_agent",
        "chat": "responder",
    },
)
```

with:

```python
workflow.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {
        "tasks_agent": "tasks_agent",
        "calendar_agent": "calendar_agent",
        "chat": "responder",
    },
)
```

- [ ] **Step 5: Update agent loops**

Replace:

```python
for agent in ["jira_agent", "tasks_agent", "calendar_agent", "story_agent"]:
    workflow.add_conditional_edges(
        agent,
        should_continue,
        {"tools": "tools", END: END},
    )
```

with:

```python
for agent in ["tasks_agent", "calendar_agent"]:
    workflow.add_conditional_edges(
        agent,
        should_continue,
        {"tools": "tools", END: END},
    )
```

- [ ] **Step 6: Update tool node return routing**

Replace:

```python
workflow.add_conditional_edges(
    "tools",
    lambda state: state.get("current_agent", "responder"),
    {
        "jira_agent": "jira_agent",
        "tasks_agent": "tasks_agent",
        "calendar_agent": "calendar_agent",
        "story_agent": "story_agent",
        "responder": "responder",
    },
)
```

with:

```python
workflow.add_conditional_edges(
    "tools",
    lambda state: state.get("current_agent", "responder"),
    {
        "tasks_agent": "tasks_agent",
        "calendar_agent": "calendar_agent",
        "responder": "responder",
    },
)
```

- [ ] **Step 7: Commit**

```bash
git add backend/agent_graph/graph.py
git commit -m "chore: reduce graph to tasks and calendar agents"
```

---

## Task 5: Update backend environment and dependencies

**Files:**
- Modify: `backend/.env.example`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Replace `.env.example` content**

```dotenv
GOOGLE_API_KEY=your-google-api-key
GOOGLE_MODEL=gemini-2.5-flash
GOOGLE_FALLBACK_MODEL=gemini-1.5-flash
DATABASE_URL=file:./frontend/drizzle/data.db
AGILE_LOG_LEVEL=INFO
AGILE_LOG_FORMAT=text
```

- [ ] **Step 2: Remove `mcp` from requirements**

Replace:

```text
langgraph>=0.2.0
langchain>=0.3.0
langchain-community>=0.3.0
langchain-google-genai>=2.0.0
langchain-core>=0.3.0
httpx>=0.27.0
python-dotenv>=1.0.0
pydantic>=2.0.0
mcp>=1.0.0
```

with:

```text
langgraph>=0.2.0
langchain>=0.3.0
langchain-community>=0.3.0
langchain-google-genai>=2.0.0
langchain-core>=0.3.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

Note: `httpx` is removed because it was only used by the Jira client.

- [ ] **Step 3: Commit**

```bash
git add backend/.env.example backend/requirements.txt
git commit -m "chore: remove jira env vars and mcp dependency"
```

---

## Task 6: Remove obsolete frontend API routes

**Files:**
- Delete: `frontend/app/api/config/route.ts`
- Delete: `frontend/app/api/tasks/[id]/publish/route.ts`

- [ ] **Step 1: Delete the routes**

```bash
rm frontend/app/api/config/route.ts
rm frontend/app/api/tasks/id/publish/route.ts
```

Use the actual path:

```bash
rm "frontend/app/api/tasks/[id]/publish/route.ts"
```

- [ ] **Step 2: Verify deletions**

```bash
git status --short
```

Expected: `D` entries for both files.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/api/config/route.ts "frontend/app/api/tasks/[id]/publish/route.ts"
git commit -m "chore: remove jira config and task publish api routes"
```

---

## Task 7: Remove ConfigChecker usage

**Files:**
- Delete: `frontend/components/ConfigChecker.tsx`
- Modify: `frontend/app/layout.tsx`

- [ ] **Step 1: Delete ConfigChecker component**

```bash
rm frontend/components/ConfigChecker.tsx
```

- [ ] **Step 2: Remove ConfigChecker from layout**

Open `frontend/app/layout.tsx`, find the `<ConfigChecker />` usage and delete it. Keep the rest of the layout unchanged.

- [ ] **Step 3: Commit**

```bash
git add frontend/components/ConfigChecker.tsx frontend/app/layout.tsx
git commit -m "chore: remove jira/google config checker"
```

---

## Task 8: Simplify task UI (remove Jira publish)

**Files:**
- Modify: `frontend/components/tasks/TaskCard.tsx`
- Modify: `frontend/components/tasks/TaskList.tsx`

- [ ] **Step 1: Replace TaskCard with the simplified version**

```tsx
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"

interface TaskCardProps {
  id: number
  title: string
  status: string
  priority: string
  dueDate: string | null
}

const priorityConfig: Record<string, { border: string; badge: string }> = {
  low:    { border: "border-l-gray-400",    badge: "bg-gray-100 text-gray-800" },
  medium: { border: "border-l-blue-400",    badge: "bg-blue-100 text-blue-800" },
  high:   { border: "border-l-orange-400",  badge: "bg-orange-100 text-orange-800" },
  critical: { border: "border-l-red-400",   badge: "bg-red-100 text-red-800" },
}

export function TaskCard({ title, status, priority, dueDate }: TaskCardProps) {
  const config = priorityConfig[priority] || priorityConfig.low

  return (
    <div className={cn("rounded-xl border border-border/40 bg-background/60 backdrop-blur-md shadow-sm transition-shadow hover:shadow-md border-l-4", config.border)}>
      <div className="p-4">
        <div className="space-y-2">
          <h3 className="font-medium">{title}</h3>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className={config.badge}>{priority}</Badge>
            <Badge variant="outline">{status}</Badge>
          </div>
          {dueDate && <p className="text-sm text-muted-foreground">Due: {dueDate}</p>}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Replace TaskList with the simplified version**

```tsx
"use client"

import { useState, useEffect } from "react"
import { TaskCard } from "./TaskCard"

interface Task {
  id: number
  title: string
  status: string
  priority: string
  dueDate: string | null
}

export function TaskList() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("/api/tasks")
      .then((res) => res.json())
      .then((data) => setTasks(data.tasks))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-4">Loading tasks...</div>

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <TaskCard key={task.id} {...task} />
      ))}
      {tasks.length === 0 && <p className="text-muted-foreground">No tasks yet.</p>}
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/components/tasks/TaskCard.tsx frontend/components/tasks/TaskList.tsx
git commit -m "chore: remove publish-to-jira from task ui"
```

---

## Task 9: Update dashboard KPIs

**Files:**
- Modify: `frontend/components/dashboard/DashboardGrid.tsx`
- Modify: `frontend/components/dashboard/DashboardHome.tsx`

- [ ] **Step 1: Replace DashboardGrid**

```tsx
"use client"

import { useState, useEffect } from "react"
import { KpiCard } from "./KpiCard"

export function DashboardGrid() {
  const [tasks, setTasks] = useState<{ tasks: { status: string }[] }>({ tasks: [] })
  const [events, setEvents] = useState<{ events: { title: string; eventDate: string }[] }>({ events: [] })

  useEffect(() => {
    fetch("/api/tasks").then(r => r.json()).then(setTasks)
    fetch("/api/calendar").then(r => r.json()).then(setEvents)
  }, [])

  const pendingTasks = tasks.tasks.filter(t => t.status === "pending").length
  const upcomingDeadlines = events.events.slice(0, 5)

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <KpiCard title="Pending Tasks" value={pendingTasks} description="Open tasks" />
      <KpiCard title="Upcoming Deadlines" value={upcomingDeadlines.length} description="Next events" />
      <KpiCard title="Total Tasks" value={tasks.tasks.length} description="All local tasks" />
    </div>
  )
}
```

- [ ] **Step 2: Replace DashboardHome**

```tsx
"use client"

import { useState, useEffect } from "react"
import { KpiCard } from "./KpiCard"
import { TaskCard } from "@/components/tasks/TaskCard"
import { GlassCard } from "@/components/ui/glass-card"
import { ListChecks, CalendarDays } from "lucide-react"

interface Task {
  id: number
  title: string
  status: string
  priority: string
  dueDate: string | null
}

interface CalendarEvent {
  id: number
  title: string
  eventDate: string
  eventType: string
  source: string
}

export function DashboardHome() {
  const [tasks, setTasks] = useState<{ tasks: Task[] }>({ tasks: [] })
  const [events, setEvents] = useState<{ events: CalendarEvent[] }>({ events: [] })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch("/api/tasks").then(r => r.json()),
      fetch("/api/calendar").then(r => r.json()),
    ]).then(([tasksData, eventsData]) => {
      setTasks(tasksData)
      setEvents(eventsData)
    }).finally(() => setLoading(false))
  }, [])

  const today = new Date().toISOString().split("T")[0]

  const todayTasks = tasks.tasks.filter(t => t.dueDate === today && t.status === "pending")
  const todayEvents = events.events.filter(e => e.eventDate === today)
  const pendingTasks = tasks.tasks.filter(t => t.status === "pending").length

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-semibold mb-1">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Loading your day...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">{today} &mdash; Here&apos;s your day</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <KpiCard title="Pending Tasks" value={pendingTasks} description="Open tasks" />
        <KpiCard title="Today&apos;s Events" value={todayEvents.length} description="Events today" />
        <KpiCard title="Total Tasks" value={tasks.tasks.length} description="All local tasks" />
      </div>

      <GlassCard>
        <div className="flex items-center gap-2 mb-4">
          <ListChecks className="h-5 w-5 text-primary" />
          <h2 className="text-base font-semibold">Today&apos;s Tasks</h2>
        </div>
        {todayTasks.length > 0 ? (
          <div className="space-y-2">
            {todayTasks.map((task) => (
              <TaskCard key={task.id} {...task} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No tasks due today.</p>
        )}
      </GlassCard>

      <GlassCard>
        <div className="flex items-center gap-2 mb-4">
          <CalendarDays className="h-5 w-5 text-primary" />
          <h2 className="text-base font-semibold">Today&apos;s Events</h2>
        </div>
        {todayEvents.length > 0 ? (
          <div className="space-y-2">
            {todayEvents.map((event) => (
              <div key={event.id} className="flex items-center gap-3 rounded-lg border border-border/30 bg-background/40 px-4 py-3">
                <span className={`h-2 w-2 rounded-full ${
                  event.eventType === "deadline" ? "bg-destructive" :
                  event.eventType === "milestone" ? "bg-blue-500" :
                  "bg-green-500"
                }`} />
                <span className="font-medium text-sm">{event.title}</span>
                <span className="text-xs text-muted-foreground">({event.eventType})</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No events today.</p>
        )}
      </GlassCard>
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/components/dashboard/DashboardGrid.tsx frontend/components/dashboard/DashboardHome.tsx
git commit -m "chore: remove jira-related kpis from dashboard"
```

---

## Task 10: Clean projects API route

**Files:**
- Modify: `frontend/app/api/projects/route.ts`

- [ ] **Step 1: Remove `jiraKey` from project creation**

Replace:

```typescript
const project = await db.insert(projects).values({
  name: body.name,
  jiraKey: body.jira_key || null,
  description: body.description || "",
}).returning()
```

with:

```typescript
const project = await db.insert(projects).values({
  name: body.name,
  description: body.description || "",
}).returning()
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/api/projects/route.ts
git commit -m "chore: remove jira_key from projects api"
```

---

## Task 11: Update Drizzle schema and regenerate migrations

**Files:**
- Modify: `frontend/drizzle/schema.ts`
- Modify: `frontend/drizzle/migrations/schema.ts`
- Modify: `frontend/drizzle/migrations/relations.ts`
- Delete: existing migration SQL files (if any)
- Create: new migration SQL files

- [ ] **Step 1: Update `frontend/drizzle/schema.ts`**

```typescript
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core"
import { sql } from "drizzle-orm"

export const projects = sqliteTable("projects", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  name: text("name").notNull(),
  description: text("description"),
  createdAt: text("created_at").default(sql`(datetime('now'))`),
})

export const localTasks = sqliteTable("local_tasks", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  title: text("title").notNull(),
  description: text("description"),
  status: text("status").default("pending"),
  priority: text("priority").default("medium"),
  dueDate: text("due_date"),
  projectId: integer("project_id").references(() => projects.id),
  createdAt: text("created_at").default(sql`(datetime('now'))`),
})

export const chatHistory = sqliteTable("chat_history", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  role: text("role").notNull(),
  content: text("content").notNull(),
  createdAt: text("created_at").default(sql`(datetime('now'))`),
})

export const calendarEvents = sqliteTable("calendar_events", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  title: text("title").notNull(),
  eventDate: text("event_date").notNull(),
  eventType: text("event_type").notNull(),
  source: text("source").default("local"),
  projectId: integer("project_id").references(() => projects.id),
  createdAt: text("created_at").default(sql`(datetime('now'))`),
})
```

- [ ] **Step 2: Regenerate Drizzle artifacts**

From the `frontend` directory:

```bash
cd frontend
npx drizzle-kit generate
```

If `drizzle-kit` is not installed or `generate` is not the correct command for this Drizzle version, inspect `package.json` scripts and use the appropriate command.

- [ ] **Step 3: Delete the old SQLite database**

```bash
rm -f frontend/drizzle/data.db
```

- [ ] **Step 4: Apply the new migration**

```bash
cd frontend
npx drizzle-kit migrate
```

Or run the generated SQL against `frontend/drizzle/data.db` with `sqlite3`.

- [ ] **Step 5: Verify schema**

```bash
sqlite3 frontend/drizzle/data.db ".schema"
```

Expected: no `jira_key`, `jira_issue_id`, or `synced` columns.

- [ ] **Step 6: Commit**

```bash
git add frontend/drizzle/
git commit -m "chore: remove jira columns from sqlite schema and regenerate migrations"
```

---

## Task 12: Rewrite README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the README content**

Use this minimal version:

```markdown
# Agile Agent — Local Task & Calendar Assistant

Sistema multiagente conversacional para gestionar tareas locales y eventos de calendario. Construido con LangGraph + Next.js.

## Arquitectura

```
Frontend (Next.js 16) ↔ API Routes ↔ LangGraph (Python)
                                        ├── Tasks Agent (SQLite local)
                                        └── Calendar Agent
```

El flujo comienza en el chat del frontend, que envía el mensaje a una API Route de Next.js. Esta levanta un subproceso Python que ejecuta el grafo de LangGraph: un **Supervisor** (LLM) clasifica la intención y deriva al agente especializado, que usa sus herramientas y devuelve la respuesta vía SSE.

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 16, TypeScript, React 19, Tailwind CSS v4, shadcn/ui |
| Agentes | LangGraph, LangChain, Gemini 2.0 Flash |
| Base de datos | SQLite via Drizzle ORM |
| Streaming | Server-Sent Events (SSE) |
| Contenerización | Docker Compose |

## Getting Started

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # configurar GOOGLE_API_KEY
```

### Frontend

```bash
cd frontend
cp .env.example .env.local   # solo DATABASE_URL (base local)
npm install
npm run dev                   # http://localhost:3000
```

El backend se ejecuta automáticamente como subproceso desde Next.js al enviar un mensaje.

### Trazabilidad y logs

El backend emite trazas estructuradas para cada interacción:

- Inicio y fin de cada invocación al grafo (`session_id`, número de mensajes, agente final).
- Decisiones del supervisor (mensaje de entrada y agente seleccionado).
- Invocaciones de cada agente con el mensaje recibido y la respuesta generada.
- Llamadas a herramientas: nombre, argumentos y resultado.
- Errores con contexto completo.

Puedes controlar el formato y nivel mediante variables de entorno en `backend/.env`:

```
AGILE_LOG_LEVEL=INFO        # DEBUG | INFO | WARNING | ERROR
AGILE_LOG_FORMAT=text       # text | json
```

Las trazas aparecen en `stderr` del subproceso Python y se muestran en la consola de Next.js.

### Estados visuales del chat

El panel de chat muestra indicadores claros de estado:

- **Procesando**: avatar pulsante, puntos animados y etiqueta del agente activo.
- **Error**: mensaje resaltado en rojo con icono de alerta y banner inferior.
- **Agente activo**: cada respuesta del asistente muestra la etiqueta del agente que la generó (`Tasks Agent`, `Calendar Agent`, etc.).

### Variables de entorno

Las credenciales sensibles se configuran en `backend/.env`:

```
GOOGLE_API_KEY=your-google-api-key
DATABASE_URL=file:./frontend/drizzle/data.db
```

El frontend solo necesita `DATABASE_URL` en `frontend/.env.local` para la base SQLite local.

## Estructura del proyecto

```
├── frontend/
│   ├── app/                    # Páginas y API routes (App Router)
│   │   ├── page.tsx            # Chat principal
│   │   ├── calendar/
│   │   ├── tasks/
│   │   ├── dashboard/
│   │   └── api/                # API routes (chat, tasks, calendar, projects)
│   ├── components/             # UI components
│   │   ├── chat/               # ChatStream, ChatInput, ChatMessage
│   │   ├── calendar/           # CalendarView
│   │   ├── tasks/              # TaskCard, TaskList
│   │   ├── dashboard/          # DashboardGrid, KpiCard
│   │   └── ui/                 # shadcn/ui primitives
│   ├── drizzle/                # Schema SQLite + migraciones
│   └── lib/                    # DB client, utils
├── backend/
│   ├── agent_graph/            # LangGraph agents
│   │   ├── graph.py            # Grafo principal
│   │   ├── supervisor.py       # Router LLM
│   │   ├── tasks_agent.py      # Tareas locales
│   │   └── calendar_agent.py   # Eventos y deadlines
│   ├── tools/                  # Herramientas (tool decorator)
│   ├── .env.example            # Template de variables de entorno
│   ├── pyproject.toml
│   └── requirements.txt
├── docs/                       # Documentación y especificaciones
├── docker-compose.yml
├── AGENTS.md                   # Instrucciones para agentes IA
└── README.md
```

## Agentes

| Agente | Función | Herramientas |
|---|---|---|
| **Supervisor** | Router LLM — clasifica el mensaje y deriva al agente correcto | Gemini 2.0 Flash |
| **Tasks Agent** | Crear, listar, actualizar y eliminar tareas locales | `create_task`, `list_tasks`, `update_task`, `delete_task` |
| **Calendar Agent** | Eventos, deadlines, milestones | `get_calendar_events`, `get_upcoming_deadlines`, `add_calendar_event` |

## Branching Strategy

Este repositorio sigue una estrategia estricta de ramas:

- **`main`** — Solo para pases a producción.
- **`develop`** — Integración de todo el trabajo mediante merges.
- **`feature/<name>`** — Nuevas funcionalidades.
- **`fix/<name>`** — Correcciones.
- **`docs/<name>`** — Documentación y configuración.

Queda prohibido commitear directamente a `develop` o `main`. Ver `AGENTS.md` para el flujo detallado.

## Próximos pasos

- [ ] Autenticación multi-usuario (NextAuth / Clerk)
- [ ] Tests automatizados (pytest para agentes, Vitest para frontend)
- [ ] Migración a PostgreSQL (desde SQLite)
- [ ] Chat por voz (Web Speech API)
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite readme for tasks and calendar only"
```

---

## Task 13: Update docker-compose.yml

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Remove Jira environment variables**

Find the `environment:` section and delete:

```yaml
- JIRA_URL=${JIRA_URL}
- JIRA_EMAIL=${JIRA_EMAIL}
- JIRA_API_TOKEN=${JIRA_API_TOKEN}
- JIRA_MCP_SERVER=${JIRA_MCP_SERVER}
```

Keep `GOOGLE_API_KEY`, `DATABASE_URL`, and any other non-Jira variables.

- [ ] **Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "chore: remove jira env vars from docker compose"
```

---

## Task 14: Final verification

- [ ] **Step 1: Search for remaining Jira / Story references**

```bash
grep -R -i -n "jira\|story_agent\|refine_story\|split_story\|estimate_effort\|publish.*jira" backend frontend docs README.md docker-compose.yml --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.next --exclude-dir=.git
```

Expected: only matches in historical spec/plan documents under `docs/superpowers/` (which are intentionally kept) and possibly in `.git` history. No matches in active code.

- [ ] **Step 2: Check Python syntax**

```bash
cd backend
python3 -m py_compile agent_graph/graph.py agent_graph/supervisor.py agent_graph/tasks_agent.py agent_graph/calendar_agent.py tools/tasks_tools.py tools/calendar_tools.py run_graph.py
```

Expected: no output (success).

- [ ] **Step 3: Check frontend build**

```bash
cd frontend
npm run build
```

Expected: build completes with exit code 0.

- [ ] **Step 4: Run type checks (if available)**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no TypeScript errors.

- [ ] **Step 5: Final status check**

```bash
git status --short
```

Expected: all changes committed; working tree clean.

---

## Spec Coverage

| Spec requirement | Implementing task(s) |
|---|---|
| Remove `backend/agent_graph/jira_agent.py` | Task 1 |
| Remove `backend/agent_graph/story_agent.py` | Task 1 |
| Remove `backend/mcp/` | Task 1 |
| Remove `backend/tools/jira_tools.py` | Task 1 |
| Remove `backend/tools/story_tools.py` | Task 1 |
| Remove `publish_task_to_jira` | Task 2 |
| Supervisor only routes to tasks/calendar/chat | Task 3 |
| Graph only contains tasks/calendar/responder/tools nodes | Task 4 |
| Remove Jira env vars and MCP dependency | Task 5 |
| Remove frontend config + publish API routes | Task 6 |
| Remove ConfigChecker | Task 7 |
| Remove publish UI from tasks | Task 8 |
| Remove Jira-related dashboard KPIs | Task 9 |
| Remove `jiraKey` from projects API | Task 10 |
| Remove Jira columns from schema and regenerate migrations | Task 11 |
| Rewrite README | Task 12 |
| Remove Jira env vars from docker-compose | Task 13 |
| Verify no remaining references | Task 14 |
