import { NextRequest } from "next/server"
import { spawn } from "child_process"
import path from "path"

interface ChatPayload {
  message: string
  previous_messages?: { role: string; content: string }[]
  session_id?: string
}

function encodeEvent(payload: object) {
  return `data: ${JSON.stringify(payload)}\n\n`
}

export async function POST(req: NextRequest) {
  const { message, previous_messages, session_id } = (await req.json()) as ChatPayload

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      try {
        const scriptPath = path.join(process.cwd(), "..", "backend", "run_graph.py")
        const python = spawn("python3", [scriptPath], {
          cwd: path.join(process.cwd(), ".."),
        })

        python.stdin.write(
          JSON.stringify({
            message,
            session_id,
            previous_messages: previous_messages || [],
          })
        )
        python.stdin.end()

        let fullOutput = ""

        python.stdout.on("data", (data: Buffer) => {
          fullOutput += data.toString()
        })

        python.on("close", (code) => {
          try {
            if (code !== 0) {
              let errorMsg = `Graph execution failed (exit code ${code})`
              try {
                const err = JSON.parse(fullOutput.trim())
                if (err.error) errorMsg = err.error
              } catch {}
              controller.enqueue(encoder.encode(encodeEvent({ type: "error", error: errorMsg })))
            } else {
              const trimmed = fullOutput.trim()
              try {
                const result = JSON.parse(trimmed)
                if (result.agent) {
                  controller.enqueue(encoder.encode(encodeEvent({ type: "agent", agent: result.agent })))
                }
                if (result.content !== undefined) {
                  controller.enqueue(encoder.encode(encodeEvent({ type: "chunk", content: result.content })))
                }
              } catch {
                controller.enqueue(encoder.encode(encodeEvent({ type: "chunk", content: trimmed })))
              }
            }
          } finally {
            controller.enqueue(encoder.encode(encodeEvent({ type: "done" })))
            controller.close()
          }
        })

        python.stderr.on("data", (data: Buffer) => {
          const text = data.toString()
          console.error("Python stderr:", text)
          // Forward backend logs/traces as debug events so the UI can optionally display them.
          controller.enqueue(encoder.encode(encodeEvent({ type: "trace", level: "stderr", message: text })))
        })
      } catch (error) {
        controller.enqueue(
          encoder.encode(encodeEvent({ type: "error", error: String(error) }))
        )
        controller.enqueue(encoder.encode(encodeEvent({ type: "done" })))
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
