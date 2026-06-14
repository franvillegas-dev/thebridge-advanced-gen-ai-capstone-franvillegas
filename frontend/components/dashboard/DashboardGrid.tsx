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
