"use client"

import { cn } from "@/lib/utils"
import { getAgentLabel } from "./ChatContext"
import { Bot } from "lucide-react"

interface ChatLoadingIndicatorProps {
  agent?: string | null
}

export function ChatLoadingIndicator({ agent }: ChatLoadingIndicatorProps) {
  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[80%]">
        <div className="mb-1 flex items-center gap-1.5 px-1">
          <span className="text-[10px] uppercase tracking-wider font-medium text-muted-foreground">
            {getAgentLabel(agent)}
          </span>
        </div>
        <div
          className={cn(
            "rounded-xl px-4 py-3 text-sm backdrop-blur-sm border border-border/30 bg-muted/30 text-foreground",
            "flex items-center gap-3"
          )}
        >
          <Bot className="h-4 w-4 text-primary animate-pulse" />
          <div className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
            <span className="h-1.5 w-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
            <span className="h-1.5 w-1.5 rounded-full bg-primary animate-bounce" />
          </div>
          <span className="text-xs text-muted-foreground">Processing...</span>
        </div>
      </div>
    </div>
  )
}
