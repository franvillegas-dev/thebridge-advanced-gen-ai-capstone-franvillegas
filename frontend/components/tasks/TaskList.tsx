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
