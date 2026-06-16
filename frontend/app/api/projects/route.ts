import { NextRequest, NextResponse } from "next/server"
import { db } from "@/lib/db"
import { projects } from "@/drizzle/schema"

export async function GET() {
  const allProjects = await db.select().from(projects)
  return NextResponse.json({ projects: allProjects })
}

export async function POST(req: NextRequest) {
  const body = await req.json()
  const project = await db.insert(projects).values({
    name: body.name,
    description: body.description || "",
  }).returning()
  return NextResponse.json({ project: project[0] }, { status: 201 })
}
