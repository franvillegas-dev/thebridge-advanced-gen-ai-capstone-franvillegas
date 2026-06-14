import { NextRequest, NextResponse } from "next/server"
import { db } from "@/lib/db"
import { calendarEvents } from "@/drizzle/schema"
import { eq, and, gte, lte } from "drizzle-orm"

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const startDate = searchParams.get("start_date")
  const endDate = searchParams.get("end_date")
  const projectId = searchParams.get("project_id")

  let conditions = []
  if (startDate) conditions.push(gte(calendarEvents.eventDate, startDate))
  if (endDate) conditions.push(lte(calendarEvents.eventDate, endDate))
  if (projectId) conditions.push(eq(calendarEvents.projectId, parseInt(projectId)))

  const query = db.select().from(calendarEvents)
  const events = conditions.length > 0 ? await query.where(and(...conditions)) : await query
  return NextResponse.json({ events })
}

export async function POST(req: NextRequest) {
  const body = await req.json()
  const event = await db.insert(calendarEvents).values({
    title: body.title,
    eventDate: body.event_date,
    eventType: body.event_type || "deadline",
    source: body.source || "local",
    projectId: body.project_id || null,
  }).returning()
  return NextResponse.json({ event: event[0] }, { status: 201 })
}
