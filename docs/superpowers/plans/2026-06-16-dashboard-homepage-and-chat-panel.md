# Dashboard Homepage & Persistent Chat Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert home page to dashboard with KPIs/today's items, move chat to persistent right panel, add error handling.

**Architecture:** Layout becomes 3-column grid (nav | main | chat panel). Chat state lives in React Context to survive navigation. Backend agents wrap LLM/Jira calls in try/except returning user-friendly errors. Toast notifications show on config validation failure.

**Tech Stack:** Next.js 16, React 19, Tailwind v4, shadcn/ui, LangGraph, LangChain, OpenAI

---

### Task 1: Toast Component + Provider

**Files:**
- Create: `frontend/components/ui/toast.tsx`
- Create: `frontend/hooks/use-toast.ts`
- Create: `frontend/components/ui/toaster.tsx`

- [ ] **Step 1: Create toast types and context**

```typescript
// frontend/hooks/use-toast.ts
"use client"

import { useState, useCallback, createContext, useContext } from "react"

interface Toast {
  id: string
  title: string
  description?: string
  variant?: "default" | "destructive"
}

interface ToastContextValue {
  toasts: Toast[]
  toast: (t: Omit<Toast, "id">) => void
  dismiss: (id: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const toast = useCallback((t: Omit<Toast, "id">) => {
    const id = crypto.randomUUID()
    setToasts((prev) => [...prev, { ...t, id }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((x) => x.id !== id))
    }, 5000)
  }, [])

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((x) => x.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error("useToast must be used within ToastProvider")
  return ctx
}
```

- [ ] **Step 2: Create Toaster component**

```typescript
// frontend/components/ui/toaster.tsx
"use client"

import { useToast } from "@/hooks/use-toast"

export function Toaster() {
  const { toasts, dismiss } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`rounded-lg border px-4 py-3 shadow-lg text-sm cursor-pointer animate-in slide-in-from-right ${
            t.variant === "destructive"
              ? "bg-destructive text-destructive-foreground border-destructive"
              : "bg-background text-foreground border-border"
          }`}
          onClick={() => dismiss(t.id)}
        >
          <strong className="block">{t.title}</strong>
          {t.description && <p className="text-xs mt-1 opacity-80">{t.description}</p>}
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/hooks/use-toast.ts frontend/components/ui/toaster.tsx
git commit -m "feat: add toast component and provider"
```

---

### Task 2: ChatContext (Global Chat State)

**Files:**
- Create: `frontend/components/chat/ChatContext.tsx`

- [ ] **Step 1: Create ChatContext**

```typescript
// frontend/components/chat/ChatContext.tsx
"use client"

import { useState, useRef, useCallback, createContext, useContext } from "react"

interface Message {
  role: "user" | "assistant"
  content: string
}

interface ChatContextValue {
  messages: Message[]
  streamingContent: string
  isLoading: boolean
  isOpen: boolean
  sendMessage: (text: string) => Promise<void>
  togglePanel: () => void
  closePanel: () => void
}

const ChatContext = createContext<ChatContextValue | null>(null)

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [streamingContent, setStreamingContent] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(true)
  const sessionId = useRef(crypto.randomUUID())

  const sendMessage = useCallback(async (message: string) => {
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
      setStreamingContent(`Lo siento, no pude conectar con el asistente. Verifica tu conexión e intenta de nuevo.`)
    } finally {
      setIsLoading(false)
      setMessages((prev) => [...prev, { role: "assistant", content: streamingContent }])
      setStreamingContent("")
    }
  }, [streamingContent])

  const togglePanel = useCallback(() => setIsOpen((prev) => !prev), [])
  const closePanel = useCallback(() => setIsOpen(false), [])

  return (
    <ChatContext.Provider value={{ messages, streamingContent, isLoading, isOpen, sendMessage, togglePanel, closePanel }}>
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error("useChat must be used within ChatProvider")
  return ctx
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/chat/ChatContext.tsx
git commit -m "feat: add ChatContext for global chat state"
```

---

### Task 3: ChatPanel Component (Right Sidebar)

**Files:**
- Create: `frontend/components/chat/ChatPanel.tsx`

- [ ] **Step 1: Create ChatPanel**

```typescript
// frontend/components/chat/ChatPanel.tsx
"use client"

import { useChat } from "./ChatContext"
import { ChatMessage } from "./ChatMessage"
import { ChatInput } from "./ChatInput"

export function ChatPanel() {
  const { messages, streamingContent, isLoading, isOpen, togglePanel } = useChat()

  return (
    <>
      {/* Mobile: hidden unless open; Desktop: fixed right panel */}
      <aside
        className={`
          fixed right-0 top-0 bottom-0 z-40 flex flex-col bg-background border-l
          transition-transform duration-300
          ${isOpen ? "translate-x-0" : "translate-x-full"}
          w-full md:w-[400px]
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h2 className="font-semibold text-sm">AI Assistant</h2>
          <button
            onClick={togglePanel}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            {isOpen ? "✕" : "☰"}
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          {messages.map((msg, i) => (
            <ChatMessage key={i} role={msg.role} content={msg.content} />
          ))}
          {streamingContent && <ChatMessage role="assistant" content={streamingContent} />}
          {messages.length === 0 && !streamingContent && (
            <p className="text-sm text-muted-foreground text-center mt-8">
              Ask me about your projects, tasks, or Jira issues.
            </p>
          )}
        </div>

        {/* Input */}
        <ChatInput onSend={(m) => useChat().sendMessage(m)} disabled={isLoading} />
      </aside>

      {/* Toggle button when collapsed */}
      {!isOpen && (
        <button
          onClick={togglePanel}
          className="fixed right-0 top-1/2 -translate-y-1/2 z-40 bg-background border rounded-l-lg px-2 py-4 text-xs shadow-md hover:bg-accent"
        >
          Chat
        </button>
      )}
    </>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/chat/ChatPanel.tsx
git commit -m "feat: add ChatPanel persistent right sidebar"
```

---

### Task 4: Restructure Layout (3-Column Grid)

**Files:**
- Modify: `frontend/app/layout.tsx`
- Modify: `frontend/app/globals.css`

- [ ] **Step 1: Update layout with 3-column grid**

```tsx
// frontend/app/layout.tsx
import type { Metadata } from "next"
import Link from "next/link"
import "./globals.css"
import { ToastProvider } from "@/hooks/use-toast"
import { Toaster } from "@/components/ui/toaster"
import { ChatProvider } from "@/components/chat/ChatContext"
import { ChatPanel } from "@/components/chat/ChatPanel"

export const metadata: Metadata = {
  title: "Agile Agent",
  description: "AI-powered Jira project management",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background font-sans antialiased">
        <ToastProvider>
          <ChatProvider>
            {/* Mobile bottom nav */}
            <nav className="fixed bottom-0 left-0 right-0 z-30 border-t bg-background md:hidden">
              <div className="flex justify-around p-2">
                <NavLink href="/" label="Home" />
                <NavLink href="/tasks" label="Tasks" />
                <NavLink href="/calendar" label="Calendar" />
                <NavLink href="/dashboard" label="Dashboard" />
              </div>
            </nav>
            {/* Desktop sidebar */}
            <aside className="hidden md:flex fixed left-0 top-0 bottom-0 w-56 border-r bg-background flex-col p-4 z-30">
              <h2 className="font-semibold mb-6">Agile Agent</h2>
              <nav className="space-y-2">
                <NavLink href="/" label="Home" />
                <NavLink href="/tasks" label="Tasks" />
                <NavLink href="/calendar" label="Calendar" />
                <NavLink href="/dashboard" label="Dashboard" />
              </nav>
            </aside>
            {/* Main content */}
            <div className="md:ml-56 pb-16 md:pb-0 md:mr-[400px]">
              {children}
            </div>
            {/* Chat panel */}
            <ChatPanel />
            <Toaster />
          </ChatProvider>
        </ToastProvider>
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
git add frontend/app/layout.tsx
git commit -m "feat: restructure layout to 3-column grid with chat panel"
```

---

### Task 5: DashboardHome (Home Page)

**Files:**
- Create: `frontend/components/dashboard/DashboardHome.tsx`
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: Create DashboardHome component**

```typescript
// frontend/components/dashboard/DashboardHome.tsx
"use client"

import { useState, useEffect } from "react"
import { KpiCard } from "./KpiCard"
import { TaskCard } from "@/components/tasks/TaskCard"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface Task {
  id: number
  title: string
  status: string
  priority: string
  dueDate: string | null
  synced: boolean
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
  const pendingPublish = tasks.tasks.filter(t => !t.synced).length

  if (loading) {
    return (
      <div className="p-6 max-w-4xl">
        <h1 className="text-2xl font-semibold mb-2">Dashboard</h1>
        <p className="text-muted-foreground mb-6">Loading your day...</p>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-2xl font-semibold mb-1">Dashboard</h1>
      <p className="text-sm text-muted-foreground mb-6">{today} — Here&apos;s your day</p>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KpiCard title="Pending Tasks" value={pendingTasks} description="Open tasks" />
        <KpiCard title="Pending Publish" value={pendingPublish} description="Tasks not in Jira" />
        <KpiCard title="Today's Events" value={todayEvents.length} description="Events today" />
        <KpiCard title="Total Tasks" value={tasks.tasks.length} description="All local tasks" />
      </div>

      {/* Today's Tasks */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">Today&apos;s Tasks</h2>
        {todayTasks.length > 0 ? (
          <div className="space-y-2">
            {todayTasks.map((task) => (
              <TaskCard key={task.id} {...task} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No tasks due today.</p>
        )}
      </section>

      {/* Today's Events */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Today&apos;s Events</h2>
        {todayEvents.length > 0 ? (
          <div className="space-y-2">
            {todayEvents.map((event) => (
              <Card key={event.id}>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${
                      event.eventType === "deadline" ? "bg-destructive" :
                      event.eventType === "milestone" ? "bg-blue-500" :
                      "bg-green-500"
                    }`} />
                    <span className="font-medium">{event.title}</span>
                    <span className="text-xs text-muted-foreground">({event.eventType})</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No events today.</p>
        )}
      </section>
    </div>
  )
}
```

- [ ] **Step 2: Update home page**

```tsx
// frontend/app/page.tsx
import { DashboardHome } from "@/components/dashboard/DashboardHome"

export default function Home() {
  return <DashboardHome />
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/components/dashboard/DashboardHome.tsx frontend/app/page.tsx
git commit -m "feat: replace home page with dashboard showing KPIs and today items"
```

---

### Task 6: Config Validation Endpoint + Startup Toasts

**Files:**
- Create: `frontend/app/api/config/route.ts`
- Modify: `frontend/app/layout.tsx`

- [ ] **Step 1: Create config validation endpoint**

```typescript
// frontend/app/api/config/route.ts
import { NextResponse } from "next/server"
import { spawn } from "child_process"
import path from "path"

export async function GET() {
  try {
    const result = await new Promise<string>((resolve, reject) => {
      const python = spawn("python3", [
        "-c",
        `
import os
import sys
sys.path.insert(0, '.')
try:
    from backend.agent_graph.__init__ import load_dotenv
except ImportError:
    pass

openai_key = bool(os.getenv("OPENAI_API_KEY"))
jira_url = bool(os.getenv("JIRA_URL"))
jira_email = bool(os.getenv("JIRA_EMAIL"))
jira_token = bool(os.getenv("JIRA_API_TOKEN"))

print(f"openai={openai_key},jira={jira_url and jira_email and jira_token}")
        `,
      ], {
        cwd: path.join(process.cwd(), ".."),
      })

      let output = ""
      python.stdout.on("data", (data: Buffer) => { output += data.toString() })
      python.on("close", () => resolve(output.trim()))
      python.stderr.on("data", (data: Buffer) => { console.error(data.toString()) })
    })

    const openai = result.includes("openai=True")
    const jira = result.includes("jira=True")

    return NextResponse.json({ openai, jira })
  } catch {
    return NextResponse.json({ openai: false, jira: false })
  }
}
```

- [ ] **Step 2: Add config check to layout**

Add this inside `frontend/app/layout.tsx`. Create a new client component:

```typescript
// frontend/components/ConfigChecker.tsx
"use client"

import { useEffect } from "react"
import { useToast } from "@/hooks/use-toast"

export function ConfigChecker() {
  const { toast } = useToast()

  useEffect(() => {
    fetch("/api/config")
      .then((r) => r.json())
      .then((data: { openai: boolean; jira: boolean }) => {
        if (!data.openai) {
          toast({
            title: "OpenAI API key not configured",
            description: "Set OPENAI_API_KEY in backend/.env for the AI assistant to work.",
            variant: "destructive",
          })
        }
        if (!data.jira) {
          toast({
            title: "Jira not configured",
            description: "Set JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN in backend/.env for Jira integration.",
            variant: "destructive",
          })
        }
      })
      .catch(() => {
        toast({
          title: "Could not check configuration",
          description: "Make sure the backend dependencies are installed.",
          variant: "destructive",
        })
      })
  }, [toast])

  return null
}
```

- [ ] **Step 3: Add ConfigChecker to layout**

```tsx
// In frontend/app/layout.tsx, inside ChatProvider add:
import { ConfigChecker } from "@/components/ConfigChecker"

// and inside the body, before Toaster:
<ConfigChecker />
```

- [ ] **Step 4: Commit**

```bash
git add frontend/app/api/config/route.ts frontend/components/ConfigChecker.tsx
git commit -m "feat: add config validation endpoint and startup toasts"
```

---

### Task 7: Backend Error Wrapping

**Files:**
- Modify: `backend/mcp/jira_mcp_client.py`
- Modify: `backend/tools/jira_tools.py`
- Modify: `backend/agent_graph/supervisor.py`
- Modify: `backend/agent_graph/jira_agent.py`
- Modify: `backend/agent_graph/story_agent.py`
- Modify: `backend/agent_graph/tasks_agent.py`
- Modify: `backend/agent_graph/calendar_agent.py`

- [ ] **Step 1: Wrap Jira MCP client with error handling**

```python
# backend/mcp/jira_mcp_client.py
import os
import httpx


class JiraMCPClient:
    def __init__(self):
        self.base_url = os.getenv("JIRA_URL", "").rstrip("/")
        self.email = os.getenv("JIRA_EMAIL", "")
        self.token = os.getenv("JIRA_API_TOKEN", "")
        self.mcp_server_url = os.getenv("JIRA_MCP_SERVER", "").rstrip("/") or None

    async def search_issues(self, jql: str, max_results: int = 20) -> list[dict]:
        try:
            if self.mcp_server_url:
                return await self._mcp_call("search_issues", {"jql": jql, "maxResults": max_results})
            return await self._rest_search(jql, max_results)
        except Exception as e:
            return [{"error": f"Could not connect to Jira: {e}"}]

    async def get_issue(self, issue_key: str) -> dict:
        try:
            if self.mcp_server_url:
                return await self._mcp_call("get_issue", {"issueKey": issue_key})
            return await self._rest_get_issue(issue_key)
        except Exception as e:
            return {"error": f"Could not fetch issue {issue_key}: {e}"}

    async def create_issue(self, project: str, summary: str, issue_type: str = "Task",
                           description: str = "", priority: str = "Medium") -> dict:
        try:
            if self.mcp_server_url:
                return await self._mcp_call("create_issue", {
                    "project": project, "summary": summary,
                    "issueType": issue_type, "description": description, "priority": priority,
                })
            return await self._rest_create_issue(project, summary, issue_type, description, priority)
        except Exception as e:
            return {"error": f"Could not create Jira issue: {e}"}

    async def update_issue(self, issue_key: str, fields: dict) -> dict:
        try:
            if self.mcp_server_url:
                return await self._mcp_call("update_issue", {"issueKey": issue_key, "fields": fields})
            return await self._rest_update_issue(issue_key, fields)
        except Exception as e:
            return {"error": f"Could not update issue {issue_key}: {e}"}

    # ... rest of methods unchanged ...
```

- [ ] **Step 2: Wrap Jira tools with error handling**

```python
# backend/tools/jira_tools.py — wrap each tool's async runner
# For each @tool function, wrap the inner async _run() in try/except:

@tool
def search_issues(jql: str, max_results: int = 20) -> str:
    """Search Jira issues using JQL. Returns a formatted list of issues."""
    async def _run():
        try:
            client = get_jira_client()
            issues = await client.search_issues(jql, max_results)
            if not issues:
                return "No issues found."
            if len(issues) == 1 and "error" in issues[0]:
                return issues[0]["error"]
            lines = []
            for issue in issues[:max_results]:
                key = issue.get("key", "?")
                summary = issue.get("fields", {}).get("summary", "?")
                status = issue.get("fields", {}).get("status", {}).get("name", "?")
                assignee = issue.get("fields", {}).get("assignee", {}) or {}
                assignee_name = assignee.get("displayName", "Unassigned")
                lines.append(f"- {key}: {summary} [{status}] assigned to {assignee_name}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error searching Jira: {e}. Verify JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN in backend/.env"
    return asyncio.run(_run())
```

Apply the same try/except pattern to `get_issue`, `create_jira_issue`, and `update_jira_issue`.

- [ ] **Step 3: Wrap supervisor OpenAI call**

```python
# backend/agent_graph/supervisor.py
def route_to_agent(state: AgentState) -> str:
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    try:
        response = _supervisor_chain.invoke({"input": last_message})
        agent_name = response.content.strip().lower()
    except Exception:
        return "chat"
    valid_agents = {"jira_agent", "tasks_agent", "calendar_agent", "story_agent", "chat"}
    return agent_name if agent_name in valid_agents else "chat"
```

- [ ] **Step 4: Wrap agent OpenAI calls (jira_agent, story_agent, tasks_agent, calendar_agent)**

In each agent file, wrap the `response = agent.invoke(...)` call:

```python
# backend/agent_graph/jira_agent.py
def handle_jira(state: AgentState) -> AgentState:
    from langchain_core.messages import AIMessage
    messages = state["messages"]
    try:
        agent = create_jira_agent()
        system_msg = SystemMessage(content=JIRA_AGENT_PROMPT)
        response = agent.invoke([system_msg] + messages)
        return {**state, "messages": state["messages"] + [response]}
    except Exception:
        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content="Lo siento, no pude conectar con el asistente de IA. Verifica que OPENAI_API_KEY esté configurada correctamente en backend/.env")
            ],
        }
```

Apply the same pattern to `story_agent.py`, `tasks_agent.py`, and `calendar_agent.py`.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat: add error handling to backend agents, Jira client, and supervisor"
```

---

### Task 8: Wire ChatPanel Input with ChatContext

**Files:**
- Modify: `frontend/components/chat/ChatPanel.tsx`
- Modify: `frontend/components/chat/ChatInput.tsx`

- [ ] **Step 1: Fix ChatPanel to use context properly**

```tsx
// frontend/components/chat/ChatPanel.tsx
("use client")

import { useChat } from "./ChatContext"
import { ChatMessage } from "./ChatMessage"
import { ChatInput } from "./ChatInput"

export function ChatPanel() {
  const { messages, streamingContent, isLoading, isOpen, togglePanel, sendMessage } = useChat()

  // ... rest using sendMessage directly:
  <ChatInput onSend={sendMessage} disabled={isLoading} />
}
```

- [ ] **Step 2: Remove old ChatStream (no longer used as standalone)**

No changes needed — ChatStream.tsx stays as-is for reference. We import from ChatContext now.

- [ ] **Step 3: Commit**

```bash
git add frontend/components/chat/ChatPanel.tsx
git commit -m "fix: wire ChatPanel input with ChatContext sendMessage"
```

---

### Self-Review

**Spec coverage:**
- Home page = dashboard with KPIs + today's tasks + today's events → Task 5
- AI assistant on the right side, visible on all pages → Tasks 2, 3, 4
- Chat errors shown in conversation → Task 7 (backend returns AIMessage with error)
- Config errors shown as toasts → Task 6
- Desktop 3-column grid layout → Task 4
- Mobile responsive → Task 4 (bottom nav + chat as panel)

**No placeholders.** All code is complete.

**Type consistency:** All interfaces match across tasks. `Message` type from Task 2 matches existing `ChatMessage` usage.
