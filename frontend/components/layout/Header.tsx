import { LayoutDashboard } from "lucide-react"

export function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between h-14 border-b border-border/40 bg-background/80 px-6 backdrop-blur-xl">
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
