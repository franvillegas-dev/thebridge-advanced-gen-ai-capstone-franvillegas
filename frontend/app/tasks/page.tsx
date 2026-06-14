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
