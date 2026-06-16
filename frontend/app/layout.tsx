import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
})
import { ToastProvider } from "@/hooks/use-toast"
import { Toaster } from "@/components/ui/toaster"
import { ChatProvider } from "@/components/chat/ChatContext"
import { ChatPanel } from "@/components/chat/ChatPanel"
import { ConfigChecker } from "@/components/ConfigChecker"
import { SidebarDesktop, SidebarMobile } from "@/components/layout/SidebarNav"
import { Header } from "@/components/layout/Header"

export const metadata: Metadata = {
  title: "Agile Agent",
  description: "AI-powered Jira project management",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-background font-sans antialiased">
        <ToastProvider>
          <ChatProvider>
            <Header />
            <SidebarMobile />
            <SidebarDesktop />
            <div className="pt-14 md:ml-56 pb-16 md:pb-0 md:mr-[400px]">
              <main className="p-6 max-w-5xl mx-auto space-y-8">
                {children}
              </main>
            </div>
            <ConfigChecker />
            <ChatPanel />
            <Toaster />
          </ChatProvider>
        </ToastProvider>
      </body>
    </html>
  )
}
