"use client"

import { useChat } from "./ChatContext"
import { ChatMessage } from "./ChatMessage"
import { ChatInput } from "./ChatInput"

export function ChatPanel() {
  const { messages, streamingContent, isLoading, isOpen, togglePanel, sendMessage } = useChat()

  return (
    <>
      <aside
        className={`
          fixed right-0 top-0 bottom-0 z-40 flex flex-col bg-background border-l
          transition-transform duration-300
          ${isOpen ? "translate-x-0" : "translate-x-full"}
          w-full md:w-[400px]
        `}
      >
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h2 className="font-semibold text-sm">AI Assistant</h2>
          <button
            onClick={togglePanel}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            {isOpen ? "✕" : "☰"}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {messages.map((msg, i) => (
            <ChatMessage key={i} role={msg.role} content={msg.content} />
          ))}
          {streamingContent && <ChatMessage role="assistant" content={streamingContent} />}
          {messages.length === 0 && !streamingContent && (
            <p className="text-sm text-muted-foreground text-center mt-8">
              Ask me about your projects, tasks, or Jira issues.
            </p>
          )}
        </div>

        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </aside>

      {!isOpen && (
        <button
          onClick={togglePanel}
          className="fixed right-0 top-1/2 -translate-y-1/2 z-40 bg-background border rounded-l-lg px-2 py-4 text-xs shadow-md hover:bg-accent"
        >
          Chat
        </button>
      )}
    </>
  )
}
