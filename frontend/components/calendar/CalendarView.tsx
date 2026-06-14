"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

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
    fetch("/api/calendar")
      .then((res) => res.json())
      .then((data) => setEvents(data.events))
      .finally(() => setLoading(false))
  }, [])

  const grouped = events.reduce<Record<string, CalendarEvent[]>>((acc, event) => {
    const key = event.eventDate
    if (!acc[key]) acc[key] = []
    acc[key].push(event)
    return acc
  }, {})

  if (loading) return <div className="p-4">Loading calendar...</div>

  return (
    <div className="space-y-4">
      {Object.entries(grouped).sort().map(([date, dateEvents]) => (
        <Card key={date}>
          <CardHeader>
            <CardTitle className="text-lg">{date}</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {dateEvents.map((event) => (
                <li key={event.id} className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    event.eventType === "deadline" ? "bg-destructive" :
                    event.eventType === "milestone" ? "bg-blue-500" :
                    "bg-green-500"
                  }`} />
                  <span>{event.title}</span>
                  <span className="text-xs text-muted-foreground">({event.eventType})</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ))}
      {events.length === 0 && <p className="text-muted-foreground p-4">No calendar events.</p>}
    </div>
  )
}
