import { NextRequest } from "next/server"
import { spawn } from "child_process"
import path from "path"

export async function POST(req: NextRequest) {
  const { message, session_id } = await req.json()

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      try {
        const python = spawn("python3", [
          "-c",
          `
import asyncio
import sys
sys.path.insert(0, '.')
from backend.agent_graph.graph import graph
from langchain_core.messages import HumanMessage

state = {"messages": [HumanMessage(content="${message}")], "current_agent": None, "pending_publish": [], "context": {}}
result = graph.invoke(state)
print(result["messages"][-1].content)
          `,
        ], {
          cwd: path.join(process.cwd(), ".."),
        })

        python.stdout.on("data", (data: Buffer) => {
          controller.enqueue(encoder.encode(`data: ${data.toString()}\n\n`))
        })

        python.on("close", () => {
          controller.enqueue(encoder.encode("data: [DONE]\n\n"))
          controller.close()
        })

        python.stderr.on("data", (data: Buffer) => {
          console.error("Python error:", data.toString())
        })
      } catch (error) {
        controller.enqueue(encoder.encode(`data: Error: ${error}\n\n`))
        controller.close()
      }
    },
  })

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  })
}
