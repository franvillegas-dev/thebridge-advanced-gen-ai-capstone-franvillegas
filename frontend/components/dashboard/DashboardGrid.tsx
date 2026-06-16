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
