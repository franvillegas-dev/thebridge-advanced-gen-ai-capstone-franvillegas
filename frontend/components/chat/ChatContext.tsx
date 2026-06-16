"use client"

import { useState, useRef, useCallback, createContext, useContext, useEffect } from "react"
import { emitRefresh, type RefreshTarget } from "@/lib/events"

export interface Message {
  role: "user" | "assistant"
  content: string
  agent?: string
  error?: boolean
  createdEntity?: { type: "task" | "calendar_event"; data: unknown }
}

interface StreamEvent {
  type: "start" | "agent" | "chunk" | "error" | "done" | "trace" | "response"
  agent?: string
  content?: string
  error?: string
  message?: string
  level?: string
  created_entity?: { type: "task" | "calendar_event"; data: unknown }
  refresh?: RefreshTarget[]
}

interface ChatContextValue {
  messages: Message[]
  streamingContent: string
  isLoading: boolean
  isOpen: boolean
  activeAgent: string | null
  error: string | null
  sendMessage: (text: string) => Promise<void>
  togglePanel: () => void
  closePanel: () => void
  clearError: () => void
}

const ChatContext = createContext<ChatContextValue | null>(null)

const AGENT_LABELS: Record<string, string> = {
  tasks_agent: "Tasks Agent",
  calendar_agent: "Calendar Agent",
  chat: "Assistant",
}

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [streamingContent, setStreamingContent] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(true)
  const [activeAgent, setActiveAgent] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const sessionId = useRef(crypto.randomUUID())
  const streamingRef = useRef("")
  const activeAgentRef = useRef<string | null>(null)
  const messagesRef = useRef<Message[]>([])
  const pendingResponseRef = useRef<{ created_entity?: { type: "task" | "calendar_event"; data: unknown }; refresh?: RefreshTarget[] } | null>(null)

  useEffect(() => {
    messagesRef.current = messages
  }, [messages])

  const clearError = useCallback(() => setError(null), [])

  const sendMessage = useCallback(async (message: string) => {
    setMessages((prev) => [...prev, { role: "user", content: message }])
    setIsLoading(true)
    setStreamingContent("")
    setError(null)
    setActiveAgent(null)
    streamingRef.current = ""
    activeAgentRef.current = null

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          session_id: sessionId.current,
          previous_messages: messagesRef.current,
        }),
      })

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error("No response stream available")
      }

      const decoder = new TextDecoder()
      let buffer = ""
      let streamError: string | null = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          const payload = line.slice(6)
          if (payload === "[DONE]") continue

          let event: StreamEvent
          try {
            event = JSON.parse(payload)
          } catch {
            // Fallback for legacy plain-text events.
            streamingRef.current += payload.replace(/\\n/g, "\n")
            setStreamingContent(streamingRef.current)
            continue
          }

          switch (event.type) {
            case "start":
              setIsLoading(true)
              break
            case "agent":
              if (event.agent) {
                activeAgentRef.current = event.agent
                setActiveAgent(event.agent)
              }
              break
            case "chunk":
              if (event.content !== undefined) {
                streamingRef.current += event.content
                setStreamingContent(streamingRef.current)
              }
              break
            case "error":
              streamError = event.error || "Unknown error"
              break
            case "trace":
              // Backend traces are intentionally ignored by the UI but visible in the console.
              if (event.message) {
                console.log("[backend trace]", event.message.trim())
              }
              break
            case "response":
              if (event.agent) {
                activeAgentRef.current = event.agent
                setActiveAgent(event.agent)
              }
              if (event.content !== undefined) {
                streamingRef.current = event.content
                setStreamingContent(event.content)
              }
              if (event.created_entity || event.refresh) {
                pendingResponseRef.current = {
                  created_entity: event.created_entity,
                  refresh: event.refresh,
                }
              }
              break
          }
        }
      }

      if (streamError) {
        setError(streamError)
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: streamError,
            agent: activeAgentRef.current || undefined,
            error: true,
          },
        ])
      } else {
        const finalContent = streamingRef.current
        const finalAgent = activeAgentRef.current || undefined
        const entity = pendingResponseRef.current?.created_entity
        const refreshTargets = pendingResponseRef.current?.refresh

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: finalContent,
            agent: finalAgent,
            createdEntity: entity,
          },
        ])

        if (refreshTargets) {
          refreshTargets.forEach((target) => emitRefresh(target))
        }
      }
    } catch {
      const msg = "Lo siento, no pude conectar con el asistente. Verifica tu conexión e intenta de nuevo."
      setError(msg)
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: msg, error: true },
      ])
    } finally {
      setIsLoading(false)
      setStreamingContent("")
      setActiveAgent(null)
      streamingRef.current = ""
      activeAgentRef.current = null
      pendingResponseRef.current = null
    }
  }, [])

  const togglePanel = useCallback(() => setIsOpen((prev) => !prev), [])
  const closePanel = useCallback(() => setIsOpen(false), [])

  return (
    <ChatContext.Provider
      value={{
        messages,
        streamingContent,
        isLoading,
        isOpen,
        activeAgent,
        error,
        sendMessage,
        togglePanel,
        closePanel,
        clearError,
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error("useChat must be used within ChatProvider")
  return ctx
}

export function getAgentLabel(agent?: string | null) {
  return (agent && AGENT_LABELS[agent]) || "Assistant"
}
