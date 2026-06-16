"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { LayoutDashboard, ListChecks, CalendarDays } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/tasks", label: "Tasks", icon: ListChecks },
  { href: "/calendar", label: "Calendar", icon: CalendarDays },
]

export function SidebarDesktop() {
  const pathname = usePathname()

  return (
    <aside className="hidden md:flex fixed left-0 top-0 bottom-0 w-56 flex-col z-30 border-r border-border/40 bg-background/80 p-4 backdrop-blur-xl">
      <div className="flex items-center gap-2 mb-8 px-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
          <LayoutDashboard className="h-4 w-4 text-primary" />
        </div>
        <span className="font-semibold">Agile Agent</span>
      </div>
      <nav className="space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all",
                isActive
                  ? "border-l-2 border-primary bg-primary/10 font-medium text-foreground"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}

export function SidebarMobile() {
  const pathname = usePathname()

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 border-t border-border/40 bg-background/80 backdrop-blur-xl md:hidden">
      <div className="flex justify-around p-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center gap-1 rounded-lg px-3 py-2 text-xs transition-colors",
                isActive
                  ? "text-primary"
                  : "text-muted-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
