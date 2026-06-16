import { cn } from "@/lib/utils"

interface KpiCardProps {
  title: string
  value: string | number
  description?: string
  className?: string
}

export function KpiCard({ title, value, description, className }: KpiCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border/40 bg-background/60 p-5 shadow-sm backdrop-blur-md transition-shadow hover:shadow-md",
        className
      )}
    >
      <p className="text-sm font-medium text-muted-foreground">{title}</p>
      <p className="mt-1 text-3xl font-bold tracking-tight">{value}</p>
      {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
    </div>
  )
}
