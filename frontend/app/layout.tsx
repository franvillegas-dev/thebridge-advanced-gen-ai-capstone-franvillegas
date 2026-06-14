import type { Metadata } from "next"
import Link from "next/link"
import "./globals.css"

export const metadata: Metadata = {
  title: "Agile Agent",
  description: "AI-powered Jira project management",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
        {/* Mobile bottom nav */}
        <nav className="fixed bottom-0 left-0 right-0 border-t bg-background md:hidden">
          <div className="flex justify-around p-2">
            <NavLink href="/" label="Chat" />
            <NavLink href="/tasks" label="Tasks" />
            <NavLink href="/calendar" label="Calendar" />
            <NavLink href="/dashboard" label="Dashboard" />
          </div>
        </nav>
        {/* Desktop sidebar */}
        <aside className="hidden md:flex fixed left-0 top-0 bottom-0 w-56 border-r bg-background flex-col p-4">
          <h2 className="font-semibold mb-6">Agile Agent</h2>
          <nav className="space-y-2">
            <NavLink href="/" label="Chat" />
            <NavLink href="/tasks" label="Tasks" />
            <NavLink href="/calendar" label="Calendar" />
            <NavLink href="/dashboard" label="Dashboard" />
          </nav>
        </aside>
        {/* Desktop main content offset */}
        <div className="md:ml-56 pb-16 md:pb-0">
          {children}
        </div>
      </body>
    </html>
  )
}

function NavLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="flex items-center justify-center px-3 py-2 text-sm rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
    >
      {label}
    </Link>
  )
}
