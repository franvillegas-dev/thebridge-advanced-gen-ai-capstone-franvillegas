# UI Redesign: Glassmorphism Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply elegant glassmorphism styling across all pages while keeping sections clearly distinguishable.

**Architecture:** Reusable `GlassCard` component wraps content sections. Sidebar gets glass background + icons + active state. Cards (KPI, task, calendar, chat) get glass styling with backdrop blur and subtle borders. All pages maintain consistent section spacing with glass dividers.

**Tech Stack:** Next.js 16 + React 19, Tailwind CSS v4, lucide-react icons, shadcn/ui base-nova

---

### Task 1: Create GlassCard component

**Files:**
- Create: `frontend/components/ui/glass-card.tsx`

- [ ] **Step 1: Create GlassCard component**

```tsx
import * as React from "react"
import { cn } from "@/lib/utils"

interface GlassCardProps extends React.ComponentProps<"div"> {
  hover?: boolean
}

export function GlassCard({ className, hover = false, children, ...props }: GlassCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border/40 bg-background/60 p-6 shadow-sm backdrop-blur-md",
        hover && "transition-shadow hover:shadow-md",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
```

- [ ] **Step 2: Verify it compiles**

Run: `cd frontend && npx tsc --noEmit` (no output expected)

---

### Task 2: Update sidebar with glass effect + icons + active state

**Files:**
- Modify: `frontend/app/layout.tsx`
- Create: `frontend/components/layout/SidebarNav.tsx`

- [ ] **Step 1: Create SidebarNav client component for active state**

```tsx
"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { LayoutDashboard, ListChecks, CalendarDays } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/tasks", label: "Tasks", icon: ListChecks },
  { href: "/calendar", label: "Calendar", icon: CalendarDays },
]

export function SidebarDesktop() {
  const pathname = usePathname()

  return (
    <aside className="hidden md:flex fixed left-0 top-0 bottom-0 w-56 flex-col z-30 border-r border-border/40 bg-background/80 p-4 backdrop-blur-xl">
      <div className="flex items-center gap-2 mb-8 px-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
          <LayoutDashboard className="h-4 w-4 text-primary" />
        </div>
        <span className="font-semibold">Agile Agent</span>
      </div>
      <nav className="space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all",
                isActive
                  ? "border-l-2 border-primary bg-primary/10 font-medium text-foreground"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}

export function SidebarMobile() {
  const pathname = usePathname()

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 border-t border-border/40 bg-background/80 backdrop-blur-xl md:hidden">
      <div className="flex justify-around p-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center gap-1 rounded-lg px-3 py-2 text-xs transition-colors",
                isActive
                  ? "text-primary"
                  : "text-muted-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
```

- [ ] **Step 2: Update layout.tsx to use new sidebar components**

Replace the nav sections and aside with the client components:

```tsx
import type { Metadata } from "next"
import "./globals.css"
import { ToastProvider } from "@/hooks/use-toast"
import { Toaster } from "@/components/ui/toaster"
import { ChatProvider } from "@/components/chat/ChatContext"
import { ChatPanel } from "@/components/chat/ChatPanel"
import { ConfigChecker } from "@/components/ConfigChecker"
import { SidebarDesktop, SidebarMobile } from "@/components/layout/SidebarNav"

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
            <SidebarMobile />
            <SidebarDesktop />
            <div className="md:ml-56 pb-16 md:pb-0 md:mr-[400px]">
              <main className="p-6 max-w-5xl mx-auto space-y-8">
                {children}
              </main>
            </div>
            <ConfigChecker />
            <ChatPanel />
            <Toaster />
          </ChatProvider>
        </ToastProvider>
      </body>
    </html>
  )
}
```

- [ ] **Step 3: Clean up page wrappers (remove duplicate padding)**

Update `app/dashboard/page.tsx` (already clean, just renders `<DashboardHome />` — no change needed).

Update `app/tasks/page.tsx`: remove wrapper padding since layout now handles it:
```tsx
import { TaskList } from "@/components/tasks/TaskList"

export default function TasksPage() {
  return (
    <>
      <h1 className="text-2xl font-semibold">Tasks</h1>
      <TaskList />
    </>
  )
}
```

Update `app/calendar/page.tsx`:
```tsx
import { CalendarView } from "@/components/calendar/CalendarView"

export default function CalendarPage() {
  return (
    <>
      <h1 className="text-2xl font-semibold">Calendar</h1>
      <CalendarView />
    </>
  )
}
```

- [ ] **Step 4: Verify it compiles**

Run: `cd frontend && npx tsc --noEmit`

---

### Task 3: Update KpiCard with glass styling

**Files:**
- Modify: `frontend/components/dashboard/KpiCard.tsx`

- [ ] **Step 1: Update KpiCard**

```tsx
import { cn } from "@/lib/utils"

interface KpiCardProps {
  title: string
  value: string | number
  description?: string
  className?: string
}

export function KpiCard({ title, value, description, className }: KpiCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border/40 bg-background/60 p-5 shadow-sm backdrop-blur-md transition-shadow hover:shadow-md",
        className
      )}
    >
      <p className="text-sm font-medium text-muted-foreground">{title}</p>
      <p className="mt-1 text-3xl font-bold tracking-tight">{value}</p>
      {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
    </div>
  )
}
```

---

### Task 4: Update DashboardHome with section glass cards

**Files:**
- Modify: `frontend/components/dashboard/DashboardHome.tsx`

- [ ] **Step 1: Wrap sections in GlassCard and add section headers with icons**

```tsx
"use client"

import { useState, useEffect } from "react"
import { KpiCard } from "./KpiCard"
import { TaskCard } from "@/components/tasks/TaskCard"
import { GlassCard } from "@/components/ui/glass-card"
import { ListChecks, CalendarDays, BarChart3 } from "lucide-react"

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

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard title="Pending Tasks" value={pendingTasks} description="Open tasks" />
        <KpiCard title="Pending Publish" value={pendingPublish} description="Tasks not in Jira" />
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

---

### Task 5: Update TaskCard with glass styling and priority border

**Files:**
- Modify: `frontend/components/tasks/TaskCard.tsx`

- [ ] **Step 1: Update TaskCard**

```tsx
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

const priorityConfig: Record<string, { border: string; badge: string }> = {
  low:    { border: "border-l-gray-400",    badge: "bg-gray-100 text-gray-800" },
  medium: { border: "border-l-blue-400",    badge: "bg-blue-100 text-blue-800" },
  high:   { border: "border-l-orange-400",  badge: "bg-orange-100 text-orange-800" },
  critical: { border: "border-l-red-400",   badge: "bg-red-100 text-red-800" },
}

export function TaskCard({ id, title, status, priority, dueDate, synced, onPublish }: TaskCardProps) {
  const config = priorityConfig[priority] || priorityConfig.low

  return (
    <div className={`rounded-xl border border-border/40 bg-background/60 backdrop-blur-md shadow-sm transition-shadow hover:shadow-md border-l-4 ${config.border}`}>
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <h3 className="font-medium">{title}</h3>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className={config.badge}>{priority}</Badge>
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
              className="text-xs text-blue-600 hover:underline shrink-0"
            >
              Publish to Jira
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
```

---

### Task 6: Update CalendarView with glass styling

**Files:**
- Modify: `frontend/components/calendar/CalendarView.tsx`

- [ ] **Step 1: Update CalendarView**

```tsx
"use client"

import { useState, useEffect } from "react"
import { GlassCard } from "@/components/ui/glass-card"
import { CalendarDays } from "lucide-react"

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

  if (loading) return <p className="text-sm text-muted-foreground">Loading calendar...</p>

  if (events.length === 0) return <p className="text-sm text-muted-foreground">No calendar events.</p>

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

---

### Task 7: Update ChatPanel and ChatMessage with glass styling

**Files:**
- Modify: `frontend/components/chat/ChatPanel.tsx`
- Modify: `frontend/components/chat/ChatMessage.tsx`
- Modify: `frontend/components/chat/ChatInput.tsx`

- [ ] **Step 1: Update ChatPanel glass background**

```tsx
"use client"

import { useChat } from "./ChatContext"
import { ChatMessage } from "./ChatMessage"
import { ChatInput } from "./ChatInput"
import { X } from "lucide-react"

export function ChatPanel() {
  const { messages, streamingContent, isLoading, isOpen, togglePanel, sendMessage } = useChat()

  return (
    <>
      <aside
        className={`
          fixed right-0 top-0 bottom-0 z-40 flex flex-col
          border-l border-border/40 bg-background/90 backdrop-blur-xl
          transition-transform duration-300
          ${isOpen ? "translate-x-0" : "translate-x-full"}
          w-full md:w-[400px]
        `}
      >
        <div className="flex items-center justify-between border-b border-border/40 px-4 py-3">
          <h2 className="font-semibold text-sm">AI Assistant</h2>
          <button
            onClick={togglePanel}
            className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

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

        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </aside>

      {!isOpen && (
        <button
          onClick={togglePanel}
          className="fixed right-0 top-1/2 -translate-y-1/2 z-40 border border-border/40 bg-background/80 backdrop-blur-md rounded-l-lg px-2 py-4 text-xs shadow-sm hover:bg-accent transition-colors"
        >
          Chat
        </button>
      )}
    </>
  )
}
```

- [ ] **Step 2: Update ChatMessage with glass bubbles**

```tsx
import { cn } from "@/lib/utils"

interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={cn(
          "max-w-[80%] rounded-xl px-4 py-2.5 text-sm backdrop-blur-sm border",
          role === "user"
            ? "border-primary/20 bg-primary/15 text-foreground"
            : "border-border/30 bg-muted/30 text-foreground"
        )}
      >
        <p className="whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Update ChatInput with glass styling**

```tsx
import { useState, FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Send } from "lucide-react"

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
    <form onSubmit={handleSubmit} className="flex gap-2 border-t border-border/40 bg-background/50 p-4 backdrop-blur-sm">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={disabled}
        placeholder="Ask about your projects..."
        className="flex-1 rounded-lg border border-border/40 bg-background/60 px-3 py-2 text-sm backdrop-blur-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />
      <Button type="submit" disabled={disabled || !input.trim()} size="icon">
        <Send className="h-4 w-4" />
      </Button>
    </form>
  )
}
```

---

### Verification

- [ ] **Final check: TypeScript compilation**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors.

- [ ] **Final check: Build**

Run: `cd frontend && npm run build`
Expected: Successful build.
