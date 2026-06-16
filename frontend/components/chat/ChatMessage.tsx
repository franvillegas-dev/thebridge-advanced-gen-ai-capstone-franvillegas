import { cn } from "@/lib/utils"

interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={cn(
          "max-w-[80%] rounded-xl px-4 py-2.5 text-sm backdrop-blur-sm border",
          role === "user"
            ? "border-primary/20 bg-primary/15 text-foreground"
            : "border-border/30 bg-muted/30 text-foreground"
        )}
      >
        <p className="whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  )
}
