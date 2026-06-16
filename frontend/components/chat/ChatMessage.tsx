import { cn } from "@/lib/utils"
import { AlertCircle } from "lucide-react"
import { getAgentLabel } from "./ChatContext"

interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
  agent?: string
  error?: boolean
}

export function ChatMessage({ role, content, agent, error }: ChatMessageProps) {
  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"} mb-4`}>
      <div className="max-w-[80%]">
        {role === "assistant" && (
          <div className="mb-1 flex items-center gap-1.5 px-1">
            <span
              className={cn(
                "text-[10px] uppercase tracking-wider font-medium",
                error ? "text-destructive" : "text-muted-foreground"
              )}
            >
              {error ? "Error" : getAgentLabel(agent)}
            </span>
          </div>
        )}
        <div
          className={cn(
            "rounded-xl px-4 py-2.5 text-sm backdrop-blur-sm border",
            role === "user"
              ? "border-primary/20 bg-primary/15 text-foreground"
              : error
              ? "border-destructive/30 bg-destructive/10 text-destructive"
              : "border-border/30 bg-muted/30 text-foreground"
          )}
        >
          <div className="flex items-start gap-2">
            {error && <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />}
            <p className="whitespace-pre-wrap">{content}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
