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
