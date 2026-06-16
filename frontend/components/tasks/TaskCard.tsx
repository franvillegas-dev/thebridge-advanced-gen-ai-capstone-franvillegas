import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"

interface TaskCardProps {
  id: number
  title: string
  status: string
  priority: string
  dueDate: string | null
}

const priorityConfig: Record<string, { border: string; badge: string }> = {
  low:    { border: "border-l-gray-400",    badge: "bg-gray-100 text-gray-800" },
  medium: { border: "border-l-blue-400",    badge: "bg-blue-100 text-blue-800" },
  high:   { border: "border-l-orange-400",  badge: "bg-orange-100 text-orange-800" },
  critical: { border: "border-l-red-400",   badge: "bg-red-100 text-red-800" },
}

export function TaskCard({ title, status, priority, dueDate }: TaskCardProps) {
  const config = priorityConfig[priority] || priorityConfig.low

  return (
    <div className={cn("rounded-xl border border-border/40 bg-background/60 backdrop-blur-md shadow-sm transition-shadow hover:shadow-md border-l-4", config.border)}>
      <div className="p-4">
        <div className="space-y-2">
          <h3 className="font-medium">{title}</h3>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className={config.badge}>{priority}</Badge>
            <Badge variant="outline">{status}</Badge>
          </div>
          {dueDate && <p className="text-sm text-muted-foreground">Due: {dueDate}</p>}
        </div>
      </div>
    </div>
  )
}
