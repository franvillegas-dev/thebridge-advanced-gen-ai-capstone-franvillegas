import { CalendarView } from "@/components/calendar/CalendarView"

export default function CalendarPage() {
  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-6">Calendar</h1>
      <CalendarView />
    </div>
  )
}
