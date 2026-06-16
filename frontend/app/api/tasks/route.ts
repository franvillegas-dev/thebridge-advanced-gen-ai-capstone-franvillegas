import { NextRequest, NextResponse } from "next/server"
import { db } from "@/lib/db"
import { localTasks } from "@/drizzle/schema"
import { eq, and } from "drizzle-orm"

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const status = searchParams.get("status")
  const projectId = searchParams.get("project_id")

  let conditions = []
  if (status) conditions.push(eq(localTasks.status, status))
  if (projectId) conditions.push(eq(localTasks.projectId, parseInt(projectId)))

  const query = db.select().from(localTasks)
  const tasks = conditions.length > 0 ? await query.where(and(...conditions)) : await query
  return NextResponse.json({ tasks })
}

export async function POST(req: NextRequest) {
  const body = await req.json()
  const task = await db.insert(localTasks).values({
    title: body.title,
    description: body.description || "",
    status: "pending",
    priority: body.priority || "medium",
    dueDate: body.due_date || null,
    projectId: body.project_id || null,
  }).returning()
  return NextResponse.json({ task: task[0] }, { status: 201 })
}
