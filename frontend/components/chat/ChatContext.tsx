"use client"

import { useState, useRef, useCallback, createContext, useContext } from "react"

interface Message {
  role: "user" | "assistant"
  content: string
}

interface ChatContextValue {
  messages: Message[]
  streamingContent: string
  isLoading: boolean
  isOpen: boolean
  sendMessage: (text: string) => Promise<void>
  togglePanel: () => void
  closePanel: () => void
}

const ChatContext = createContext<ChatContextValue | null>(null)

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [streamingContent, setStreamingContent] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(true)
  const sessionId = useRef(crypto.randomUUID())
  const streamingRef = useRef("")

  const sendMessage = useCallback(async (message: string) => {
    setMessages((prev) => [...prev, { role: "user", content: message }])
    setIsLoading(true)
    setStreamingContent("")
    streamingRef.current = ""

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: sessionId.current }),
      })

      const reader = response.body?.getReader()
      if (!reader) return

      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6)
            if (data === "[DONE]") continue
            streamingRef.current += data
            setStreamingContent(streamingRef.current)
          }
        }
      }
    } catch {
      streamingRef.current = "Lo siento, no pude conectar con el asistente. Verifica tu conexión e intenta de nuevo."
      setStreamingContent(streamingRef.current)
    } finally {
      setIsLoading(false)
      setMessages((prev) => [...prev, { role: "assistant", content: streamingRef.current }])
      setStreamingContent("")
      streamingRef.current = ""
    }
  }, [])

  const togglePanel = useCallback(() => setIsOpen((prev) => !prev), [])
  const closePanel = useCallback(() => setIsOpen(false), [])

  return (
    <ChatContext.Provider value={{ messages, streamingContent, isLoading, isOpen, sendMessage, togglePanel, closePanel }}>
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error("useChat must be used within ChatProvider")
  return ctx
}
