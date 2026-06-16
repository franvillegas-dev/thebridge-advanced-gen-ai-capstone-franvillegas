import { NextResponse } from "next/server"
import { spawn } from "child_process"
import path from "path"

export async function GET() {
  try {
    const result = await new Promise<string>((resolve) => {
      const python = spawn("python3", [
        "-c",
        `
import os
import sys
sys.path.insert(0, '.')
try:
    from backend.agent_graph.__init__ import load_dotenv
except ImportError:
    pass

google_key = bool(os.getenv("GOOGLE_API_KEY"))
jira_url = bool(os.getenv("JIRA_URL"))
jira_email = bool(os.getenv("JIRA_EMAIL"))
jira_token = bool(os.getenv("JIRA_API_TOKEN"))

print(f"google={google_key},jira={jira_url and jira_email and jira_token}")
        `,
      ], {
        cwd: path.join(process.cwd(), ".."),
      })

      let output = ""
      python.stdout.on("data", (data: Buffer) => { output += data.toString() })
      python.on("close", () => resolve(output.trim()))
      python.stderr.on("data", (data: Buffer) => { console.error(data.toString()) })
    })

    const google = result.includes("google=True")
    const jira = result.includes("jira=True")

    return NextResponse.json({ google, jira })
  } catch {
    return NextResponse.json({ google: false, jira: false })
  }
}
