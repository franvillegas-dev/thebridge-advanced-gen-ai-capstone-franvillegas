import { GlassCard } from "@/components/ui/glass-card"

interface KpiCardProps {
  title: string
  value: string | number
  description?: string
  className?: string
}

export function KpiCard({ title, value, description, className }: KpiCardProps) {
  return (
    <GlassCard hover className={className}>
      <p className="text-sm font-medium text-muted-foreground">{title}</p>
      <p className="mt-1 text-3xl font-bold tracking-tight">{value}</p>
      {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
    </GlassCard>
  )
}
