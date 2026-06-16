import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface CreatedEntityCardProps {
  entity: { type: "task" | "calendar_event"; data: any }
}

export function CreatedEntityCard({ entity }: CreatedEntityCardProps) {
  if (entity.type === "task") {
    return (
      <Card className="mt-2 p-3 bg-muted/30 border-border/40">
        <div className="font-medium text-sm">{entity.data.title}</div>
        <div className="flex flex-wrap items-center gap-2 mt-1.5">
          <Badge variant="secondary" className="text-[10px]">
            {entity.data.status}
          </Badge>
          <Badge variant="secondary" className="text-[10px]">
            {entity.data.priority}
          </Badge>
          {entity.data.due_date && (
            <span className="text-[10px] text-muted-foreground">
              Due {entity.data.due_date}
            </span>
          )}
        </div>
      </Card>
    )
  }

  if (entity.type === "calendar_event") {
    return (
      <Card className="mt-2 p-3 bg-muted/30 border-border/40">
        <div className="font-medium text-sm">{entity.data.title}</div>
        <div className="text-[10px] text-muted-foreground mt-1">
          {entity.data.event_date} · {entity.data.start_time} - {entity.data.end_time}
        </div>
        <Badge variant="secondary" className="mt-1.5 text-[10px]">
          {entity.data.event_type}
        </Badge>
      </Card>
    )
  }

  return null
}