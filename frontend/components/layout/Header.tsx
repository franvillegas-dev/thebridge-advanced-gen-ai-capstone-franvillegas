import { LayoutDashboard } from "lucide-react"

export function Header() {
  return (
    <header className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
          <LayoutDashboard className="h-4 w-4 text-primary" />
        </div>
        <span className="text-lg font-semibold tracking-tight">Agile Agent</span>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
          JD
        </div>
        <span className="text-sm font-medium text-foreground">John Doe</span>
      </div>
    </header>
  )
}
