"use client"

import { useState, useEffect, useCallback } from "react"
import { onRefresh } from "@/lib/events"
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

  const loadData = useCallback(() => {
    setLoading(true)
    Promise.all([
      fetch("/api/tasks").then(r => r.json()),
      fetch("/api/calendar").then(r => r.json()),
    ]).then(([tasksData, eventsData]) => {
      setTasks(tasksData)
      setEvents(eventsData)
    }).finally(() => setLoading(false))
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
