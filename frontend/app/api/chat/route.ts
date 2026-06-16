import { NextRequest } from "next/server"
import { spawn } from "child_process"
import path from "path"

export async function POST(req: NextRequest) {
  const { message, previous_messages } = await req.json()

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      try {
        const scriptPath = path.join(process.cwd(), "..", "backend", "run_graph.py")
        const python = spawn("python3", [scriptPath], {
          cwd: path.join(process.cwd(), ".."),
        })

        python.stdin.write(JSON.stringify({ message, previous_messages: previous_messages || [] }))
        python.stdin.end()

        let fullOutput = ""

        python.stdout.on("data", (data: Buffer) => {
          fullOutput += data.toString()
        })

        python.on("close", (code) => {
          if (code !== 0) {
            let errorMsg = `Graph execution failed (exit code ${code})`
            try {
              const err = JSON.parse(fullOutput.trim())
              if (err.error) errorMsg = err.error
            } catch {}
            controller.enqueue(encoder.encode(`data: Error: ${errorMsg}\n\n`))
          } else {
            try {
              const trimmed = fullOutput.trim()
              const result = JSON.parse(trimmed)
              const safeContent = result.content.replace(/\n/g, "\\n")
              controller.enqueue(encoder.encode(`data: ${safeContent}\n\n`))
            } catch {
              const safeContent = fullOutput.trim().replace(/\n/g, "\\n")
              controller.enqueue(encoder.encode(`data: ${safeContent}\n\n`))
            }
          }
          controller.enqueue(encoder.encode("data: [DONE]\n\n"))
          controller.close()
        })

        python.stderr.on("data", (data: Buffer) => {
          console.error("Python stderr:", data.toString())
        })
      } catch (error) {
        controller.enqueue(encoder.encode(`data: Error: ${error}\n\n`))
        controller.enqueue(encoder.encode("data: [DONE]\n\n"))
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
