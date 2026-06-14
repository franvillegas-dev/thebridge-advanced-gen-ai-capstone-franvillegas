import { NextRequest, NextResponse } from "next/server"
import { db } from "@/lib/db"
import { localTasks } from "@/drizzle/schema"
import { eq } from "drizzle-orm"

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id: idStr } = await params
  const id = parseInt(idStr)
  const body = await req.json()
  const updates: Record<string, unknown> = {}
  if (body.status) updates.status = body.status
  if (body.priority) updates.priority = body.priority
  if (body.title) updates.title = body.title
  if (body.description) updates.description = body.description
  if (body.due_date) updates.dueDate = body.due_date

  const result = await db.update(localTasks).set(updates).where(eq(localTasks.id, id)).returning()
  return NextResponse.json({ task: result[0] })
}

export async function DELETE(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id: idStr } = await params
  const id = parseInt(idStr)
  await db.delete(localTasks).where(eq(localTasks.id, id))
  return NextResponse.json({ ok: true })
}
