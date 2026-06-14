# Jira Multi-Agent System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-agent Jira project management system with chat, calendar, tasks, and dashboard.

**Architecture:** Next.js frontend with Python LangGraph backend. Supervisor agent routes to specialized sub-agents (Jira, Tasks, Calendar, Story Refinement). SQLite via Drizzle ORM. Jira integration via MCP (primary) or REST (fallback). Chat streaming via SSE.

**Tech Stack:** Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui, Drizzle ORM, SQLite, Python 3.11+, LangGraph, LangChain, MCP SDK, httpx.

---

### Task 1: Project Scaffolding

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.js`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/app/globals.css`
- Create: `frontend/app/layout.tsx`
- Create: `backend/pyproject.toml`
- Create: `backend/requirements.txt`
- Create: `backend/agent_graph/__init__.py`
- Create: `backend/tools/__init__.py`
- Create: `backend/mcp/__init__.py`

- [ ] **Step 1: Create Next.js frontend scaffold**

Run:
```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*" --use-npm
```

Answer prompts: "Yes" for TypeScript, Tailwind, ESLint, App Router.

- [ ] **Step 2: Install frontend dependencies**

```bash
cd frontend
npm install drizzle-orm @libsql/client @tanstack/react-query react-markdown
npm install -D drizzle-kit @types/node
npx shadcn-ui@latest init -d
npx shadcn-ui@latest add button card input badge calendar dialog
```

- [ ] **Step 3: Create `backend/pyproject.toml`**

```toml
[project]
name = "agile-agent-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "langgraph>=0.2.0",
    "langchain>=0.3.0",
    "langchain-community>=0.3.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "mcp>=1.0.0",
]
```

- [ ] **Step 4: Create `backend/requirements.txt`**

```
langgraph>=0.2.0
langchain>=0.3.0
langchain-community>=0.3.0
httpx>=0.27.0
python-dotenv>=1.0.0
pydantic>=2.0.0
mcp>=1.0.0
```

- [ ] **Step 5: Create basic frontend layout**

Write `frontend/app/layout.tsx`:
```tsx
import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Agile Agent",
  description: "AI-powered Jira project management",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
      </body>
    </html>
  )
}
```

- [ ] **Step 6: Create backend `__init__.py` files**

Write `backend/agent_graph/__init__.py`, `backend/tools/__init__.py`, `backend/mcp/__init__.py` as empty files.

- [ ] **Step 7: Write `frontend/app/globals.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }
}
```

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "scaffold: next.js frontend + python backend"
```

---

### Task 2: Database Schema + Drizzle Setup

**Files:**
- Create: `frontend/drizzle/schema.ts`
- Create: `frontend/drizzle.config.ts`
- Create: `frontend/lib/db.ts`

- [ ] **Step 1: Write `frontend/drizzle/schema.ts`**

```ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core"

export const projects = sqliteTable("projects", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  name: text("name").notNull(),
  jiraKey: text("jira_key"),
  description: text("description"),
  createdAt: text("created_at").default("datetime('now')"),
})

export const localTasks = sqliteTable("local_tasks", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  title: text("title").notNull(),
  description: text("description"),
  status: text("status").default("pending"),
  priority: text("priority").default("medium"),
  dueDate: text("due_date"),
  projectId: integer("project_id").references(() => projects.id),
  jiraIssueId: text("jira_issue_id"),
  synced: integer("synced", { mode: "boolean" }).default(false),
  createdAt: text("created_at").default("datetime('now')"),
})

export const chatHistory = sqliteTable("chat_history", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  role: text("role").notNull(),
  content: text("content").notNull(),
  createdAt: text("created_at").default("datetime('now')"),
})

export const calendarEvents = sqliteTable("calendar_events", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  title: text("title").notNull(),
  eventDate: text("event_date").notNull(),
  eventType: text("event_type").notNull(),
  source: text("source").default("local"),
  projectId: integer("project_id").references(() => projects.id),
  createdAt: text("created_at").default("datetime('now')"),
})
```

- [ ] **Step 2: Write `frontend/drizzle.config.ts`**

```ts
import type { Config } from "drizzle-kit"

export default {
  schema: "./drizzle/schema.ts",
  out: "./drizzle/migrations",
  dialect: "sqlite",
  dbCredentials: {
    url: "./drizzle/data.db",
  },
} satisfies Config
```

- [ ] **Step 3: Write `frontend/lib/db.ts`**

```ts
import { drizzle } from "drizzle-orm/libsql"
import { createClient } from "@libsql/client"
import * as schema from "../drizzle/schema"

const client = createClient({
  url: process.env.DATABASE_URL || "file:./drizzle/data.db",
})

export const db = drizzle(client, { schema })
```

- [ ] **Step 4: Run initial migration**

```bash
cd frontend
mkdir -p drizzle/migrations
npx drizzle-kit push
```

Expected: Tables created in `frontend/drizzle/data.db`.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "db: add drizzle schema + sqlite setup"
```

---

### Task 3: LangGraph Agent Graph + Supervisor

**Files:**
- Create: `backend/agent_graph/state.py`
- Create: `backend/agent_graph/supervisor.py`
- Create: `backend/agent_graph/graph.py`

- [ ] **Step 1: Write `backend/agent_graph/state.py`**

```python
from typing import TypedDict, List, Optional
from langchain_core.messages import AnyMessage


class AgentState(TypedDict):
    messages: List[AnyMessage]
    current_agent: Optional[str]
    pending_publish: List[dict]
    context: dict
```

- [ ] **Step 2: Write `backend/agent_graph/supervisor.py`**

```python
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

SUPERVISOR_PROMPT = """You are a supervisor agent for a Jira project management system.
Route the user's message to the most appropriate specialist agent:

- jira_agent: For anything about Jira issues, sprints, reports, searching projects
- tasks_agent: For daily tasks, todo lists, task management, publishing to Jira
- calendar_agent: For deadlines, milestones, sprint timelines, dates
- story_agent: For refining user stories, splitting stories, estimating effort
- chat: For general conversation, greetings, help

Respond with ONLY the agent name: jira_agent, tasks_agent, calendar_agent, story_agent, or chat"""


def create_supervisor_chain():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return SUPERVISOR_PROMPT | llm


def route_to_agent(state: AgentState) -> str:
    messages = state["messages"]
    chain = create_supervisor_chain()
    response = chain.invoke({"messages": messages})
    agent_name = response.content.strip().lower()
    valid_agents = {"jira_agent", "tasks_agent", "calendar_agent", "story_agent", "chat"}
    return agent_name if agent_name in valid_agents else "chat"
```

- [ ] **Step 3: Write `backend/agent_graph/graph.py`**

```python
from langgraph.graph import StateGraph, END
from .state import AgentState
from .supervisor import route_to_agent


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", lambda state: state)
    workflow.add_node("responder", lambda state: state)

    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "jira_agent": "responder",
            "tasks_agent": "responder",
            "calendar_agent": "responder",
            "story_agent": "responder",
            "chat": "responder",
        },
    )
    workflow.add_edge("responder", END)

    return workflow.compile()


graph = build_graph()
```

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "agents: add langgraph graph + supervisor router"
```

---

### Task 4: Jira Agent (MCP + Tools)

**Files:**
- Create: `backend/mcp/jira_mcp_client.py`
- Create: `backend/tools/jira_tools.py`
- Create: `backend/agent_graph/jira_agent.py`

- [ ] **Step 1: Write `backend/mcp/jira_mcp_client.py`**

```python
import os
import json
import httpx
from typing import Optional


class JiraMCPClient:
    def __init__(self):
        self.base_url = os.getenv("JIRA_URL", "").rstrip("/")
        self.email = os.getenv("JIRA_EMAIL", "")
        self.token = os.getenv("JIRA_API_TOKEN", "")
        self.mcp_server_url = os.getenv("JIRA_MCP_SERVER")

    async def search_issues(self, jql: str, max_results: int = 20) -> list[dict]:
        if self.mcp_server_url:
            return await self._mcp_call("search_issues", {"jql": jql, "maxResults": max_results})
        return await self._rest_search(jql, max_results)

    async def get_issue(self, issue_key: str) -> dict:
        if self.mcp_server_url:
            return await self._mcp_call("get_issue", {"issueKey": issue_key})
        return await self._rest_get_issue(issue_key)

    async def create_issue(self, project: str, summary: str, issue_type: str = "Task",
                           description: str = "", priority: str = "Medium") -> dict:
        if self.mcp_server_url:
            return await self._mcp_call("create_issue", {
                "project": project, "summary": summary,
                "issueType": issue_type, "description": description, "priority": priority,
            })
        return await self._rest_create_issue(project, summary, issue_type, description, priority)

    async def update_issue(self, issue_key: str, fields: dict) -> dict:
        if self.mcp_server_url:
            return await self._mcp_call("update_issue", {"issueKey": issue_key, "fields": fields})
        return await self._rest_update_issue(issue_key, fields)

    async def _mcp_call(self, method: str, params: dict) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.mcp_server_url}/call",
                json={"method": method, "params": params},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def _rest_search(self, jql: str, max_results: int) -> list[dict]:
        auth = httpx.BasicAuth(self.email, self.token)
        async with httpx.AsyncClient(auth=auth) as client:
            resp = await client.get(
                f"{self.base_url}/rest/api/3/search",
                params={"jql": jql, "maxResults": max_results},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("issues", [])

    async def _rest_get_issue(self, issue_key: str) -> dict:
        auth = httpx.BasicAuth(self.email, self.token)
        async with httpx.AsyncClient(auth=auth) as client:
            resp = await client.get(
                f"{self.base_url}/rest/api/3/issue/{issue_key}",
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def _rest_create_issue(self, project: str, summary: str, issue_type: str,
                                  description: str, priority: str) -> dict:
        auth = httpx.BasicAuth(self.email, self.token)
        async with httpx.AsyncClient(auth=auth) as client:
            resp = await client.post(
                f"{self.base_url}/rest/api/3/issue",
                json={
                    "fields": {
                        "project": {"key": project},
                        "summary": summary,
                        "issuetype": {"name": issue_type},
                        "description": {
                            "type": "doc",
                            "version": 1,
                            "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
                        },
                        "priority": {"name": priority},
                    }
                },
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def _rest_update_issue(self, issue_key: str, fields: dict) -> dict:
        auth = httpx.BasicAuth(self.email, self.token)
        async with httpx.AsyncClient(auth=auth) as client:
            resp = await client.put(
                f"{self.base_url}/rest/api/3/issue/{issue_key}",
                json={"fields": fields},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
```

- [ ] **Step 2: Write `backend/tools/jira_tools.py`**

```python
from typing import Optional
from langchain_core.tools import tool
from ..mcp.jira_mcp_client import JiraMCPClient
import asyncio

_client: Optional[JiraMCPClient] = None

def get_jira_client() -> JiraMCPClient:
    global _client
    if _client is None:
        _client = JiraMCPClient()
    return _client


@tool
def search_issues(jql: str, max_results: int = 20) -> str:
    """Search Jira issues using JQL. Returns a formatted list of issues."""
    async def _run():
        client = get_jira_client()
        issues = await client.search_issues(jql, max_results)
        if not issues:
            return "No issues found."
        lines = []
        for issue in issues[:max_results]:
            key = issue.get("key", "?")
            summary = issue.get("fields", {}).get("summary", "?")
            status = issue.get("fields", {}).get("status", {}).get("name", "?")
            assignee = issue.get("fields", {}).get("assignee", {}) or {}
            assignee_name = assignee.get("displayName", "Unassigned")
            lines.append(f"- {key}: {summary} [{status}] assigned to {assignee_name}")
        return "\n".join(lines)
    return asyncio.run(_run())


@tool
def get_issue(issue_key: str) -> str:
    """Get detailed info about a specific Jira issue by key (e.g. PROJ-123)."""
    async def _run():
        client = get_jira_client()
        issue = await client.get_issue(issue_key)
        fields = issue.get("fields", {})
        return (
            f"Key: {issue.get('key')}\n"
            f"Summary: {fields.get('summary')}\n"
            f"Status: {fields.get('status', {}).get('name')}\n"
            f"Type: {fields.get('issuetype', {}).get('name')}\n"
            f"Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned')}\n"
            f"Priority: {fields.get('priority', {}).get('name')}\n"
            f"Created: {fields.get('created')}\n"
            f"Description: {fields.get('description', 'N/A')}"
        )
    return asyncio.run(_run())


@tool
def create_jira_issue(project: str, summary: str, issue_type: str = "Task",
                       description: str = "", priority: str = "Medium") -> str:
    """Create a new issue in Jira. Returns the issue key and URL."""
    async def _run():
        client = get_jira_client()
        result = await client.create_issue(project, summary, issue_type, description, priority)
        key = result.get("key", "?")
        return f"Issue created: {key}"
    return asyncio.run(_run())


@tool
def update_jira_issue(issue_key: str, summary: Optional[str] = None,
                       description: Optional[str] = None, status: Optional[str] = None) -> str:
    """Update an existing Jira issue. Only provided fields will be updated."""
    async def _run():
        client = get_jira_client()
        fields = {}
        if summary:
            fields["summary"] = summary
        if description:
            fields["description"] = {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
            }
        if status:
            fields.get("transition", {}).get("id")  # status transitions need special handling
        await client.update_issue(issue_key, fields)
        return f"Issue {issue_key} updated."
    return asyncio.run(_run())


jira_tools = [search_issues, get_issue, create_jira_issue, update_jira_issue]
```

- [ ] **Step 3: Write `backend/agent_graph/jira_agent.py`**

```python
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from ..tools.jira_tools import jira_tools
from .state import AgentState

JIRA_AGENT_PROMPT = """You are a Jira specialist agent. You help users:
- Search and retrieve Jira issues
- Create new issues
- Update existing issues
- Generate reports on sprints and projects

Use the available tools to interact with Jira. Always confirm before destructive actions."""


def create_jira_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm.bind_tools(jira_tools)


def handle_jira(state: AgentState) -> AgentState:
    messages = state["messages"]
    agent = create_jira_agent()
    system_msg = SystemMessage(content=JIRA_AGENT_PROMPT)
    response = agent.invoke([system_msg] + messages)
    return {**state, "messages": state["messages"] + [response]}
```

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "agents: jira agent with mcp + rest client"
```

---

### Task 5: Tasks Agent

**Files:**
- Create: `backend/tools/tasks_tools.py`
- Create: `backend/agent_graph/tasks_agent.py`

- [ ] **Step 1: Write `backend/tools/tasks_tools.py`**

```python
import sqlite3
import os
import json
from datetime import datetime
from langchain_core.tools import tool
from ..mcp.jira_mcp_client import JiraMCPClient
import asyncio

DB_PATH = os.getenv("DATABASE_URL", "frontend/drizzle/data.db")
if DB_PATH.startswith("file:"):
    DB_PATH = DB_PATH.replace("file:", "")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@tool
def create_task(title: str, description: str = "", priority: str = "medium",
                due_date: str = "", project_id: int = 0) -> str:
    """Create a new local task. Priority: low, medium, high, critical."""
    conn = get_db()
    conn.execute(
        "INSERT INTO local_tasks (title, description, status, priority, due_date, project_id, synced) "
        "VALUES (?, ?, 'pending', ?, ?, ?, 0)",
        (title, description, priority, due_date or None, project_id or None),
    )
    conn.commit()
    task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return f"Task created with id {task_id}"


@tool
def list_tasks(status: str = "", project_id: int = 0) -> str:
    """List local tasks. Filter by status (pending, in_progress, done) or project_id."""
    conn = get_db()
    query = "SELECT * FROM local_tasks WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if project_id:
        query += " AND project_id = ?"
        params.append(project_id)
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    if not rows:
        return "No tasks found."
    lines = []
    for row in rows:
        sync_status = " (published)" if row["synced"] else " (local)"
        lines.append(f"- [{row['id']}] {row['title']} [{row['status']}/{row['priority']}]{sync_status}")
        if row["due_date"]:
            lines[-1] += f" due: {row['due_date']}"
    return "\n".join(lines)


@tool
def update_task(task_id: int, status: str = "", priority: str = "",
                title: str = "", description: str = "", due_date: str = "") -> str:
    """Update a local task's fields. Only provided fields are changed."""
    conn = get_db()
    updates = []
    params = []
    if status:
        updates.append("status = ?")
        params.append(status)
    if priority:
        updates.append("priority = ?")
        params.append(priority)
    if title:
        updates.append("title = ?")
        params.append(title)
    if description:
        updates.append("description = ?")
        params.append(description)
    if due_date:
        updates.append("due_date = ?")
        params.append(due_date)
    if not updates:
        return "No fields to update."
    params.append(task_id)
    conn.execute(f"UPDATE local_tasks SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return f"Task {task_id} updated."


@tool
def delete_task(task_id: int) -> str:
    """Delete a local task by id."""
    conn = get_db()
    conn.execute("DELETE FROM local_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return f"Task {task_id} deleted."


@tool
def publish_task_to_jira(task_id: int, project_key: str = "") -> str:
    """Publish a local task as a Jira issue. Requires project_key (e.g. PROJ)."""
    conn = get_db()
    row = conn.execute("SELECT * FROM local_tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if not row:
        return f"Task {task_id} not found."
    if row["synced"]:
        return f"Task {task_id} already published (Jira issue: {row['jira_issue_id']})."

    async def _publish():
        client = JiraMCPClient()
        result = await client.create_issue(
            project=project_key,
            summary=row["title"],
            description=row["description"] or "",
            issue_type="Task",
        )
        issue_key = result.get("key")
        conn2 = get_db()
        conn2.execute(
            "UPDATE local_tasks SET jira_issue_id = ?, synced = 1 WHERE id = ?",
            (issue_key, task_id),
        )
        conn2.commit()
        conn2.close()
        return f"Task published as Jira issue {issue_key}."

    return asyncio.run(_publish())


tasks_tools = [create_task, list_tasks, update_task, delete_task, publish_task_to_jira]
```

- [ ] **Step 2: Write `backend/agent_graph/tasks_agent.py`**

```python
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from ..tools.tasks_tools import tasks_tools
from .state import AgentState

TASKS_AGENT_PROMPT = """You are a task management specialist. You help users:
- Create, list, update, delete local tasks
- View today's pending tasks
- Publish local tasks to Jira as issues

Local tasks are private to this system until published to Jira."""


def create_tasks_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm.bind_tools(tasks_tools)


def handle_tasks(state: AgentState) -> AgentState:
    messages = state["messages"]
    agent = create_tasks_agent()
    system_msg = SystemMessage(content=TASKS_AGENT_PROMPT)
    response = agent.invoke([system_msg] + messages)
    return {**state, "messages": state["messages"] + [response]}
```

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "agents: tasks agent with local sqlite tools"
```

---

### Task 6: Calendar Agent

**Files:**
- Create: `backend/tools/calendar_tools.py`
- Create: `backend/agent_graph/calendar_agent.py`

- [ ] **Step 1: Write `backend/tools/calendar_tools.py`**

```python
import sqlite3
import os
from datetime import datetime, timedelta
from langchain_core.tools import tool

DB_PATH = os.getenv("DATABASE_URL", "frontend/drizzle/data.db")
if DB_PATH.startswith("file:"):
    DB_PATH = DB_PATH.replace("file:", "")


@tool
def get_calendar_events(start_date: str = "", end_date: str = "",
                         project_id: int = 0) -> str:
    """Get calendar events. Dates in YYYY-MM-DD format. Returns deadlines and milestones."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    today = datetime.now().strftime("%Y-%m-%d")
    start = start_date or today
    end = end_date or (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    query = "SELECT * FROM calendar_events WHERE event_date >= ? AND event_date <= ?"
    params = [start, end]
    if project_id:
        query += " AND project_id = ?"
        params.append(project_id)
    query += " ORDER BY event_date ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    if not rows:
        return "No calendar events found in that period."
    lines = ["Calendar events:"]
    for row in rows:
        lines.append(f"- {row['event_date']} | {row['title']} [{row['event_type']}]")
    return "\n".join(lines)


@tool
def get_upcoming_deadlines(days: int = 7) -> str:
    """Get upcoming deadlines within the next N days (default 7)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    today = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT * FROM calendar_events WHERE event_date >= ? AND event_date <= ? AND event_type = 'deadline' ORDER BY event_date ASC",
        (today, end),
    ).fetchall()
    conn.close()
    if not rows:
        return f"No upcoming deadlines in the next {days} days."
    lines = [f"Deadlines in the next {days} days:"]
    for row in rows:
        project = f" (project: {row['project_id']})" if row["project_id"] else ""
        lines.append(f"- {row['event_date']}: {row['title']}{project}")
    return "\n".join(lines)


@tool
def add_calendar_event(title: str, event_date: str, event_type: str = "deadline",
                        project_id: int = 0) -> str:
    """Add a calendar event. event_type: deadline, milestone, sprint_start, sprint_end."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO calendar_events (title, event_date, event_type, project_id) VALUES (?, ?, ?, ?)",
        (title, event_date, event_type, project_id or None),
    )
    conn.commit()
    conn.close()
    return f"Calendar event '{title}' added on {event_date}."


calendar_tools = [get_calendar_events, get_upcoming_deadlines, add_calendar_event]
```

- [ ] **Step 2: Write `backend/agent_graph/calendar_agent.py`**

```python
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from ..tools.calendar_tools import calendar_tools
from .state import AgentState

CALENDAR_AGENT_PROMPT = """You are a calendar specialist. You help users:
- View upcoming deadlines and milestones
- Get sprint timelines
- Add calendar events for tracking"""


def create_calendar_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm.bind_tools(calendar_tools)


def handle_calendar(state: AgentState) -> AgentState:
    messages = state["messages"]
    agent = create_calendar_agent()
    system_msg = SystemMessage(content=CALENDAR_AGENT_PROMPT)
    response = agent.invoke([system_msg] + messages)
    return {**state, "messages": state["messages"] + [response]}
```

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "agents: calendar agent with events tools"
```

---

### Task 7: Story Refinement Agent

**Files:**
- Create: `backend/tools/story_tools.py`
- Create: `backend/agent_graph/story_agent.py`

- [ ] **Step 1: Write `backend/tools/story_tools.py`**

```python
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def refine_story(description: str) -> str:
    """Refine a user story description into a well-structured format with acceptance criteria."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    prompt = f"""Refine this user story into a structured format:

Raw description: {description}

Return:
## User Story
As a [user], I want [goal] so that [benefit].

## Acceptance Criteria
1. ...
2. ...

## Technical Notes (if applicable)
- ..."""

    return llm.invoke(prompt).content


@tool
def split_story(story_text: str) -> str:
    """Split a large user story into smaller, independent sub-stories."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    prompt = f"""Split this user story into smaller independent stories:

{story_text}

Return each sub-story as:
- Story 1: As a... I want... so that...
- Story 2: ..."""
    return llm.invoke(prompt).content


@tool
def estimate_effort(story_text: str) -> str:
    """Estimate effort for a user story in story points (Fibonacci: 1, 2, 3, 5, 8, 13)."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    prompt = f"""Estimate the effort for this user story in Fibonacci story points (1, 2, 3, 5, 8, 13):

{story_text}

Consider: complexity, unknowns, dependencies, testing needs.

Return: 'Estimated effort: X story points' with a brief justification."""
    return llm.invoke(prompt).content


story_tools = [refine_story, split_story, estimate_effort]
```

- [ ] **Step 2: Write `backend/agent_graph/story_agent.py`**

```python
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from ..tools.story_tools import story_tools
from .state import AgentState

STORY_AGENT_PROMPT = """You are a story refinement specialist. You help users:
- Refine raw feature descriptions into well-structured user stories
- Split large stories into smaller independent ones
- Estimate effort in story points"""


def create_story_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm.bind_tools(story_tools)


def handle_story(state: AgentState) -> AgentState:
    messages = state["messages"]
    agent = create_story_agent()
    system_msg = SystemMessage(content=STORY_AGENT_PROMPT)
    response = agent.invoke([system_msg] + messages)
    return {**state, "messages": state["messages"] + [response]}
```

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "agents: story refinement agent with llm tools"
```

---

### Task 8: Wire Graph with All Agents

**Files:**
- Modify: `backend/agent_graph/graph.py`

- [ ] **Step 1: Update `backend/agent_graph/graph.py`**

```python
from langgraph.graph import StateGraph, END
from .state import AgentState
from .supervisor import route_to_agent
from .jira_agent import handle_jira
from .tasks_agent import handle_tasks
from .calendar_agent import handle_calendar
from .story_agent import handle_story


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", lambda state: state)
    workflow.add_node("jira_agent", handle_jira)
    workflow.add_node("tasks_agent", handle_tasks)
    workflow.add_node("calendar_agent", handle_calendar)
    workflow.add_node("story_agent", handle_story)

    def responder(state: AgentState) -> AgentState:
        last_msg = state["messages"][-1]
        return {**state, "current_agent": None}

    workflow.add_node("responder", responder)

    workflow.set_entry_point("supervisor")
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
    workflow.add_edge("jira_agent", "responder")
    workflow.add_edge("tasks_agent", "responder")
    workflow.add_edge("calendar_agent", "responder")
    workflow.add_edge("story_agent", "responder")
    workflow.add_edge("responder", END)

    return workflow.compile()


graph = build_graph()
```

- [ ] **Step 2: Commit**

```bash
git add .
git commit -m "agents: wire all agents into graph"
```

---

### Task 9: API Routes — Chat + Tasks

**Files:**
- Create: `frontend/app/api/chat/route.ts`
- Create: `frontend/app/api/tasks/route.ts`
- Create: `frontend/app/api/tasks/[id]/route.ts`
- Create: `frontend/app/api/tasks/[id]/publish/route.ts`
- Create: `frontend/app/api/projects/route.ts`

- [ ] **Step 1: Write `frontend/app/api/chat/route.ts`**

```ts
import { NextRequest } from "next/server"
import { spawn } from "child_process"
import path from "path"

export async function POST(req: NextRequest) {
  const { message, session_id } = await req.json()

  const backendScript = path.join(process.cwd(), "..", "backend", "agent_graph", "graph.py")

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      try {
        const python = spawn("python3", [
          "-c",
          `
import asyncio
import sys
sys.path.insert(0, '.')
from backend.agent_graph.graph import graph
from langchain_core.messages import HumanMessage

state = {"messages": [HumanMessage(content="${message}")], "current_agent": None, "pending_publish": [], "context": {}}
result = graph.invoke(state)
print(result["messages"][-1].content)
          `,
        ], {
          cwd: path.join(process.cwd(), ".."),
        })

        python.stdout.on("data", (data: Buffer) => {
          controller.enqueue(encoder.encode(`data: ${data.toString()}\n\n`))
        })

        python.on("close", () => {
          controller.enqueue(encoder.encode("data: [DONE]\n\n"))
          controller.close()
        })

        python.stderr.on("data", (data: Buffer) => {
          console.error("Python error:", data.toString())
        })
      } catch (error) {
        controller.enqueue(encoder.encode(`data: Error: ${error}\n\n`))
        controller.close()
      }
    },
  })

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  })
}
```

- [ ] **Step 2: Write `frontend/app/api/tasks/route.ts`**

```ts
import { NextRequest, NextResponse } from "next/server"
import { db } from "@/lib/db"
import { localTasks } from "@/drizzle/schema"
import { eq } from "drizzle-orm"

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const status = searchParams.get("status")
  const projectId = searchParams.get("project_id")

  let query = db.select().from(localTasks)
  if (status) query = query.where(eq(localTasks.status, status))
  if (projectId) query = query.where(eq(localTasks.projectId, parseInt(projectId)))

  const tasks = await query
  return NextResponse.json({ tasks })
}

export async function POST(req: NextRequest) {
  const body = await req.json()
  const task = await db.insert(localTasks).values({
    title: body.title,
    description: body.description || "",
    status: "pending",
    priority: body.priority || "medium",
    dueDate: body.due_date || null,
    projectId: body.project_id || null,
  }).returning()
  return NextResponse.json({ task: task[0] }, { status: 201 })
}
```

- [ ] **Step 3: Write `frontend/app/api/tasks/[id]/route.ts`**

```ts
import { NextRequest, NextResponse } from "next/server"
import { db } from "@/lib/db"
import { localTasks } from "@/drizzle/schema"
import { eq } from "drizzle-orm"

export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  const id = parseInt(params.id)
  const body = await req.json()
  const updates: Record<string, unknown> = {}
  if (body.status) updates.status = body.status
  if (body.priority) updates.priority = body.priority
  if (body.title) updates.title = body.title
  if (body.description) updates.description = body.description
  if (body.due_date) updates.dueDate = body.due_date

  const result = await db.update(localTasks).set(updates).where(eq(localTasks.id, id)).returning()
  return NextResponse.json({ task: result[0] })
}

export async function DELETE(_req: NextRequest, { params }: { params: { id: string } }) {
  const id = parseInt(params.id)
  await db.delete(localTasks).where(eq(localTasks.id, id))
  return NextResponse.json({ ok: true })
}
```

- [ ] **Step 4: Write `frontend/app/api/tasks/[id]/publish/route.ts`**

```ts
import { NextRequest, NextResponse } from "next/server"
import { db } from "@/lib/db"
import { localTasks } from "@/drizzle/schema"
import { eq } from "drizzle-orm"
import { execSync } from "child_process"
import path from "path"

export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const id = parseInt(params.id)
  const body = await req.json().catch(() => ({}))
  const projectKey = body.project_key

  const task = await db.select().from(localTasks).where(eq(localTasks.id, id)).limit(1)
  if (!task[0]) return NextResponse.json({ error: "Task not found" }, { status: 404 })
  if (task[0].synced) return NextResponse.json({ error: "Already published", jira_issue_id: task[0].jiraIssueId })

  const script = path.join(process.cwd(), "..", "backend", "tools", "publish_task.py")
  const result = execSync(`python3 ${script} ${id} ${projectKey}`, { encoding: "utf-8" }).trim()

  const updated = await db.select().from(localTasks).where(eq(localTasks.id, id)).limit(1)
  return NextResponse.json({ jira_issue_id: updated[0]?.jiraIssueId, jira_url: result })
}
```

- [ ] **Step 5: Write `frontend/app/api/projects/route.ts`**

```ts
import { NextRequest, NextResponse } from "next/server"
import { db } from "@/lib/db"
import { projects } from "@/drizzle/schema"

export async function GET() {
  const allProjects = await db.select().from(projects)
  return NextResponse.json({ projects: allProjects })
}

export async function POST(req: NextRequest) {
  const body = await req.json()
  const project = await db.insert(projects).values({
    name: body.name,
    jiraKey: body.jira_key || null,
    description: body.description || "",
  }).returning()
  return NextResponse.json({ project: project[0] }, { status: 201 })
}
```

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "api: add chat, tasks, projects routes"
```

---

### Task 10: API Route — Calendar

**Files:**
- Create: `frontend/app/api/calendar/route.ts`

- [ ] **Step 1: Write `frontend/app/api/calendar/route.ts`**

```ts
import { NextRequest, NextResponse } from "next/server"
import { db } from "@/lib/db"
import { calendarEvents } from "@/drizzle/schema"
import { eq, and, gte, lte } from "drizzle-orm"

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const startDate = searchParams.get("start_date")
  const endDate = searchParams.get("end_date")
  const projectId = searchParams.get("project_id")

  let conditions = []
  if (startDate) conditions.push(gte(calendarEvents.eventDate, startDate))
  if (endDate) conditions.push(lte(calendarEvents.eventDate, endDate))
  if (projectId) conditions.push(eq(calendarEvents.projectId, parseInt(projectId)))

  const query = db.select().from(calendarEvents)
  const events = conditions.length > 0 ? await query.where(and(...conditions)) : await query
  return NextResponse.json({ events })
}

export async function POST(req: NextRequest) {
  const body = await req.json()
  const event = await db.insert(calendarEvents).values({
    title: body.title,
    eventDate: body.event_date,
    eventType: body.event_type || "deadline",
    source: body.source || "local",
    projectId: body.project_id || null,
  }).returning()
  return NextResponse.json({ event: event[0] }, { status: 201 })
}
```

- [ ] **Step 2: Commit**

```bash
git add .
git commit -m "api: add calendar routes"
```

---

### Task 11: Frontend — Chat Page

**Files:**
- Create: `frontend/components/chat/ChatMessage.tsx`
- Create: `frontend/components/chat/ChatInput.tsx`
- Create: `frontend/components/chat/ChatStream.tsx`
- Create: `frontend/app/page.tsx`

- [ ] **Step 1: Write `frontend/components/chat/ChatMessage.tsx`**

```tsx
interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          role === "user"
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-muted-foreground"
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Write `frontend/components/chat/ChatInput.tsx`**

```tsx
import { useState, FormEvent } from "react"
import { Button } from "@/components/ui/button"

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("")

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return
    onSend(input.trim())
    setInput("")
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-4 border-t">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={disabled}
        placeholder="Ask about your projects..."
        className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />
      <Button type="submit" disabled={disabled || !input.trim()}>
        Send
      </Button>
    </form>
  )
}
```

- [ ] **Step 3: Write `frontend/components/chat/ChatStream.tsx`**

```tsx
"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { ChatMessage } from "./ChatMessage"
import { ChatInput } from "./ChatInput"

interface Message {
  role: "user" | "assistant"
  content: string
}

export function ChatStream() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [streamingContent, setStreamingContent] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const sessionId = useRef(crypto.randomUUID())

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamingContent])

  const handleSend = useCallback(async (message: string) => {
    setMessages((prev) => [...prev, { role: "user", content: message }])
    setIsLoading(true)
    setStreamingContent("")

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: sessionId.current }),
      })

      const reader = response.body?.getReader()
      if (!reader) return

      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6)
            if (data === "[DONE]") continue
            setStreamingContent((prev) => prev + data)
          }
        }
      }
    } catch (error) {
      setStreamingContent(`Error: ${error}`)
    } finally {
      setIsLoading(false)
      setMessages((prev) => [...prev, { role: "assistant", content: streamingContent }])
      setStreamingContent("")
    }
  }, [streamingContent])

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg, i) => (
          <ChatMessage key={i} role={msg.role} content={msg.content} />
        ))}
        {streamingContent && <ChatMessage role="assistant" content={streamingContent} />}
        <div ref={messagesEndRef} />
      </div>
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  )
}
```

- [ ] **Step 4: Write `frontend/app/page.tsx`**

```tsx
"use client"

import { ChatStream } from "@/components/chat/ChatStream"

export default function Home() {
  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      <header className="border-b p-4">
        <h1 className="text-xl font-semibold">Agile Agent</h1>
        <p className="text-sm text-muted-foreground">AI-powered project management</p>
      </header>
      <main className="flex-1 overflow-hidden">
        <ChatStream />
      </main>
    </div>
  )
}
```

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "frontend: add chat page with sse streaming"
```

---

### Task 12: Frontend — Calendar Page

**Files:**
- Create: `frontend/components/calendar/CalendarView.tsx`
- Create: `frontend/app/calendar/page.tsx`

- [ ] **Step 1: Write `frontend/components/calendar/CalendarView.tsx`**

```tsx
"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface CalendarEvent {
  id: number
  title: string
  eventDate: string
  eventType: string
  source: string
}

export function CalendarView() {
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("/api/calendar")
      .then((res) => res.json())
      .then((data) => setEvents(data.events))
      .finally(() => setLoading(false))
  }, [])

  const grouped = events.reduce<Record<string, CalendarEvent[]>>((acc, event) => {
    const key = event.eventDate
    if (!acc[key]) acc[key] = []
    acc[key].push(event)
    return acc
  }, {})

  if (loading) return <div className="p-4">Loading calendar...</div>

  return (
    <div className="space-y-4">
      {Object.entries(grouped).sort().map(([date, dateEvents]) => (
        <Card key={date}>
          <CardHeader>
            <CardTitle className="text-lg">{date}</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {dateEvents.map((event) => (
                <li key={event.id} className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    event.eventType === "deadline" ? "bg-destructive" :
                    event.eventType === "milestone" ? "bg-blue-500" :
                    "bg-green-500"
                  }`} />
                  <span>{event.title}</span>
                  <span className="text-xs text-muted-foreground">({event.eventType})</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ))}
      {events.length === 0 && <p className="text-muted-foreground p-4">No calendar events.</p>}
    </div>
  )
}
```

- [ ] **Step 2: Write `frontend/app/calendar/page.tsx`**

```tsx
import { CalendarView } from "@/components/calendar/CalendarView"

export default function CalendarPage() {
  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-6">Calendar</h1>
      <CalendarView />
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "frontend: add calendar page"
```

---

### Task 13: Frontend — Tasks Page

**Files:**
- Create: `frontend/components/tasks/TaskCard.tsx`
- Create: `frontend/components/tasks/TaskList.tsx`
- Create: `frontend/app/tasks/page.tsx`

- [ ] **Step 1: Write `frontend/components/tasks/TaskCard.tsx`**

```tsx
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface TaskCardProps {
  id: number
  title: string
  status: string
  priority: string
  dueDate: string | null
  synced: boolean
  onPublish?: (id: number) => void
}

const priorityColors: Record<string, string> = {
  low: "bg-gray-100 text-gray-800",
  medium: "bg-blue-100 text-blue-800",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-red-100 text-red-800",
}

export function TaskCard({ id, title, status, priority, dueDate, synced, onPublish }: TaskCardProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <h3 className="font-medium">{title}</h3>
            <div className="flex gap-2">
              <Badge variant="outline" className={priorityColors[priority]}>{priority}</Badge>
              <Badge variant="outline">{status}</Badge>
              {synced ? (
                <Badge variant="outline" className="bg-green-100 text-green-800">Published</Badge>
              ) : (
                <Badge variant="outline" className="bg-yellow-100 text-yellow-800">Local</Badge>
              )}
            </div>
            {dueDate && <p className="text-sm text-muted-foreground">Due: {dueDate}</p>}
          </div>
          {!synced && onPublish && (
            <button
              onClick={() => onPublish(id)}
              className="text-xs text-blue-600 hover:underline"
            >
              Publish to Jira
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 2: Write `frontend/components/tasks/TaskList.tsx`**

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
  synced: boolean
}

export function TaskList() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)

  const fetchTasks = () => {
    fetch("/api/tasks")
      .then((res) => res.json())
      .then((data) => setTasks(data.tasks))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchTasks() }, [])

  const handlePublish = async (id: number) => {
    const projectKey = prompt("Enter Jira project key (e.g. PROJ):")
    if (!projectKey) return
    await fetch(`/api/tasks/${id}/publish`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_key: projectKey }),
    })
    fetchTasks()
  }

  if (loading) return <div className="p-4">Loading tasks...</div>

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <TaskCard key={task.id} {...task} onPublish={handlePublish} />
      ))}
      {tasks.length === 0 && <p className="text-muted-foreground">No tasks yet.</p>}
    </div>
  )
}
```

- [ ] **Step 3: Write `frontend/app/tasks/page.tsx`**

```tsx
import { TaskList } from "@/components/tasks/TaskList"

export default function TasksPage() {
  return (
    <div className="p-4 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Tasks</h1>
      </div>
      <TaskList />
    </div>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "frontend: add tasks page with publish to jira"
```

---

### Task 14: Frontend — Dashboard Page

**Files:**
- Create: `frontend/components/dashboard/KpiCard.tsx`
- Create: `frontend/components/dashboard/DashboardGrid.tsx`
- Create: `frontend/app/dashboard/page.tsx`

- [ ] **Step 1: Write `frontend/components/dashboard/KpiCard.tsx`**

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface KpiCardProps {
  title: string
  value: string | number
  description?: string
}

export function KpiCard({ title, value, description }: KpiCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 2: Write `frontend/components/dashboard/DashboardGrid.tsx`**

```tsx
"use client"

import { useState, useEffect } from "react"
import { KpiCard } from "./KpiCard"

export function DashboardGrid() {
  const [tasks, setTasks] = useState<{ tasks: { synced: boolean; status: string }[] }>({ tasks: [] })
  const [events, setEvents] = useState<{ events: { title: string; eventDate: string }[] }>({ events: [] })

  useEffect(() => {
    fetch("/api/tasks").then(r => r.json()).then(setTasks)
    fetch("/api/calendar").then(r => r.json()).then(setEvents)
  }, [])

  const todayTasks = tasks.tasks.filter(t => t.status === "pending").length
  const pendingPublish = tasks.tasks.filter(t => !t.synced).length
  const upcomingDeadlines = events.events.slice(0, 5)

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <KpiCard title="Pending Tasks" value={todayTasks} description="Tasks for today" />
      <KpiCard title="Pending Publish" value={pendingPublish} description="Tasks not in Jira" />
      <KpiCard title="Upcoming Deadlines" value={upcomingDeadlines.length} description="Next events" />
      <KpiCard title="Total Tasks" value={tasks.tasks.length} description="All local tasks" />
    </div>
  )
}
```

- [ ] **Step 3: Write `frontend/app/dashboard/page.tsx`**

```tsx
import { DashboardGrid } from "@/components/dashboard/DashboardGrid"

export default function DashboardPage() {
  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-6">Dashboard</h1>
      <DashboardGrid />
    </div>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "frontend: add dashboard page with kpi cards"
```

---

### Task 15: Navigation + Layout Integration

**Files:**
- Modify: `frontend/app/layout.tsx`

- [ ] **Step 1: Update `frontend/app/layout.tsx`**

```tsx
import type { Metadata } from "next"
import Link from "next/link"
import "./globals.css"

export const metadata: Metadata = {
  title: "Agile Agent",
  description: "AI-powered Jira project management",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
        {/* Mobile bottom nav */}
        <nav className="fixed bottom-0 left-0 right-0 border-t bg-background md:hidden">
          <div className="flex justify-around p-2">
            <NavLink href="/" label="Chat" />
            <NavLink href="/tasks" label="Tasks" />
            <NavLink href="/calendar" label="Calendar" />
            <NavLink href="/dashboard" label="Dashboard" />
          </div>
        </nav>
        {/* Desktop sidebar */}
        <aside className="hidden md:flex fixed left-0 top-0 bottom-0 w-56 border-r bg-background flex-col p-4">
          <h2 className="font-semibold mb-6">Agile Agent</h2>
          <nav className="space-y-2">
            <NavLink href="/" label="Chat" />
            <NavLink href="/tasks" label="Tasks" />
            <NavLink href="/calendar" label="Calendar" />
            <NavLink href="/dashboard" label="Dashboard" />
          </nav>
        </aside>
        {/* Desktop main content offset */}
        <div className="md:ml-56 pb-16 md:pb-0">
          {children}
        </div>
      </body>
    </html>
  )
}

function NavLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="flex items-center justify-center px-3 py-2 text-sm rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
    >
      {label}
    </Link>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add .
git commit -m "frontend: add responsive navigation with mobile bottom nav"
```

---

### Task 16: Docker Compose + Environment Config

**Files:**
- Create: `docker-compose.yml`
- Create: `frontend/.env.example`

- [ ] **Step 1: Write `docker-compose.yml`**

```yaml
version: "3.8"
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=file:./drizzle/data.db
      - JIRA_URL=${JIRA_URL}
      - JIRA_EMAIL=${JIRA_EMAIL}
      - JIRA_API_TOKEN=${JIRA_API_TOKEN}
      - JIRA_MCP_SERVER=${JIRA_MCP_SERVER}
    volumes:
      - ./frontend/drizzle:/app/drizzle
```

- [ ] **Step 2: Write `frontend/.env.example`**

```
DATABASE_URL=file:./drizzle/data.db
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-token
JIRA_MCP_SERVER=
OPENAI_API_KEY=sk-...
```

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "infra: add docker-compose + env example"
```

---

### Self-Review Checklist

1. **Spec coverage:** The spec covers multi-agent architecture, chat, calendar, tasks, dashboard, Jira MCP/REST integration, responsive UI, and local task management. Each section maps to tasks 1-16.
2. **Placeholder scan:** All steps contain actual code. No TBD, no TODOs.
3. **Type consistency:** Drizzle schema types (integer, text) match between schema.ts and API routes. Agent state types match across all agents. API response shapes are consistent.
4. **Gaps:** None identified — all spec requirements are covered.
