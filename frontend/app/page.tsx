"use client"

import { ChatStream } from "@/components/chat/ChatStream"

export default function Home() {
  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      <header className="border-b p-4">
        <h1 className="text-xl font-semibold">Agile Agent</h1>
        <p className="text-sm text-muted-foreground">AI-powered project management</p>
      </header>
      <main className="flex-1 overflow-hidden">
        <ChatStream />
      </main>
    </div>
  )
}
