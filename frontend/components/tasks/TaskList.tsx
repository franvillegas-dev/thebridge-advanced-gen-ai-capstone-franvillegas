"use client"

import { useState, useEffect } from "react"
import { onRefresh } from "@/lib/events"
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
    const load = () => {
      setLoading(true)
      fetch("/api/tasks")
        .then((res) => res.json())
        .then((data) => setTasks(data.tasks))
        .finally(() => setLoading(false))
    }
    load()
    return onRefresh("tasks", load)
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
