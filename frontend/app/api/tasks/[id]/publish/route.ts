import { NextRequest, NextResponse } from "next/server"
import { db } from "@/lib/db"
import { localTasks } from "@/drizzle/schema"
import { eq } from "drizzle-orm"
import { execSync } from "child_process"
import path from "path"

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id: idStr } = await params
  const id = parseInt(idStr)
  const body = await req.json().catch(() => ({}))
  const projectKey = body.project_key

  const task = await db.select().from(localTasks).where(eq(localTasks.id, id)).limit(1)
  if (!task[0]) return NextResponse.json({ error: "Task not found" }, { status: 404 })
  if (task[0].synced) return NextResponse.json({ error: "Already published", jira_issue_id: task[0].jiraIssueId })

  const script = path.join(process.cwd(), "..", "backend", "tools", "publish_task.py")
  const result = execSync(`python3 ${script} ${id} ${projectKey}`, { encoding: "utf-8" }).trim()

  const updated = await db.select().from(localTasks).where(eq(localTasks.id, id)).limit(1)
  return NextResponse.json({ jira_issue_id: updated[0]?.jiraIssueId, jira_url: result })
}
