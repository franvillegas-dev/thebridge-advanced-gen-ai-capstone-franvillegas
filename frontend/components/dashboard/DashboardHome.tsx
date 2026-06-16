"use client"

import { useState, useEffect } from "react"
import { KpiCard } from "./KpiCard"
import { TaskCard } from "@/components/tasks/TaskCard"
import { Card, CardContent } from "@/components/ui/card"

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
      <p className="text-sm text-muted-foreground mb-6">{today} &mdash; Here&apos;s your day</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KpiCard title="Pending Tasks" value={pendingTasks} description="Open tasks" />
        <KpiCard title="Pending Publish" value={pendingPublish} description="Tasks not in Jira" />
        <KpiCard title="Today&apos;s Events" value={todayEvents.length} description="Events today" />
        <KpiCard title="Total Tasks" value={tasks.tasks.length} description="All local tasks" />
      </div>

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
