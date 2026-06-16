"use client"

import { useState, useEffect } from "react"
import { onRefresh } from "@/lib/events"
import { GlassCard } from "@/components/ui/glass-card"
import { CalendarDays } from "lucide-react"

interface CalendarEvent {
  id: number
  title: string
  eventDate: string
  eventType: string
  source: string
}

export function CalendarView() {
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = () => {
      setLoading(true)
      fetch("/api/calendar")
        .then((res) => res.json())
        .then((data) => setEvents(data.events))
        .finally(() => setLoading(false))
    }
    load()
    return onRefresh("calendar", load)
  }, [])

  const grouped = events.reduce<Record<string, CalendarEvent[]>>((acc, event) => {
    const key = event.eventDate
    if (!acc[key]) acc[key] = []
    acc[key].push(event)
    return acc
  }, {})

  if (loading) return <p className="text-sm text-muted-foreground">Loading calendar...</p>

  if (events.length === 0) return <p className="text-sm text-muted-foreground">No calendar events.</p>

  return (
    <div className="space-y-4">
      {Object.entries(grouped).sort().map(([date, dateEvents]) => (
        <GlassCard key={date}>
          <div className="flex items-center gap-2 mb-3">
            <CalendarDays className="h-4 w-4 text-primary" />
            <h3 className="font-semibold text-sm">{date}</h3>
          </div>
          <ul className="space-y-2">
            {dateEvents.map((event) => (
              <li key={event.id} className="flex items-center gap-3 rounded-lg border border-border/30 bg-background/40 px-3 py-2">
                <span className={`h-2 w-2 shrink-0 rounded-full ${
                  event.eventType === "deadline" ? "bg-destructive" :
                  event.eventType === "milestone" ? "bg-blue-500" :
                  "bg-green-500"
                }`} />
                <span className="text-sm font-medium">{event.title}</span>
                <span className="text-xs text-muted-foreground">({event.eventType})</span>
              </li>
            ))}
          </ul>
        </GlassCard>
      ))}
    </div>
  )
}
