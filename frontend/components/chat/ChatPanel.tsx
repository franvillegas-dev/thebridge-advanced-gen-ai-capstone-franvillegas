"use client"

import { useChat } from "./ChatContext"
import { ChatMessage } from "./ChatMessage"
import { ChatInput } from "./ChatInput"
import { ChatLoadingIndicator } from "./ChatLoadingIndicator"
import { X, MessageSquare } from "lucide-react"

export function ChatPanel() {
  const { messages, streamingContent, isLoading, isOpen, togglePanel, sendMessage, activeAgent, error } = useChat()

  return (
    <>
      <aside
        className={`
          fixed right-0 top-14 bottom-0 z-40 flex flex-col
          border-l border-border/40 bg-background/90 backdrop-blur-xl
          transition-transform duration-300
          ${isOpen ? "translate-x-0" : "translate-x-full"}
          w-full md:w-[400px]
        `}
      >
        <div className="flex items-center justify-between border-b border-border/40 px-4 py-3">
          <div className="flex items-center gap-2">
            <h2 className="font-semibold text-sm">AI Assistant</h2>
            {isLoading && (
              <span className="inline-flex h-2 w-2 rounded-full bg-primary animate-pulse" />
            )}
          </div>
          <button
            onClick={togglePanel}
            className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {messages.map((msg, i) => (
            <ChatMessage
              key={i}
              role={msg.role}
              content={msg.content}
              agent={msg.agent}
              error={msg.error}
              createdEntity={msg.createdEntity}
            />
          ))}
          {streamingContent && (
            <ChatMessage role="assistant" content={streamingContent} agent={activeAgent || undefined} />
          )}
          {isLoading && !streamingContent && <ChatLoadingIndicator agent={activeAgent} />}
          {messages.length === 0 && !streamingContent && !isLoading && (
            <p className="text-sm text-muted-foreground text-center mt-8">
              Ask me about your tasks or calendar events.
            </p>
          )}
        </div>

        <div className="border-t border-border/40 bg-background/50 px-4 py-2">
          {error && (
            <div className="mb-2 rounded-md bg-destructive/10 border border-destructive/20 px-3 py-2 text-xs text-destructive">
              {error}
            </div>
          )}
          <ChatInput onSend={sendMessage} disabled={isLoading} />
        </div>
      </aside>

      {!isOpen && (
        <button
          onClick={togglePanel}
          className="fixed right-0 top-1/2 -translate-y-1/2 z-40 border border-border/40 bg-background/80 backdrop-blur-md rounded-l-lg px-2 py-4 text-xs shadow-sm hover:bg-accent transition-colors flex items-center gap-2"
        >
          <MessageSquare className="h-3.5 w-3.5" />
          Chat
          {isLoading && <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />}
        </button>
      )}
    </>
  )
}
