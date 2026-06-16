"use client"

import { useEffect } from "react"
import { useToast } from "@/hooks/use-toast"

export function ConfigChecker() {
  const { toast } = useToast()

  useEffect(() => {
    fetch("/api/config")
      .then((r) => r.json())
      .then((data: { openai: boolean; jira: boolean }) => {
        if (!data.openai) {
          toast({
            title: "OpenAI API key not configured",
            description: "Set OPENAI_API_KEY in backend/.env for the AI assistant to work.",
            variant: "destructive",
          })
        }
        if (!data.jira) {
          toast({
            title: "Jira not configured",
            description: "Set JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN in backend/.env for Jira integration.",
            variant: "destructive",
          })
        }
      })
      .catch(() => {
        toast({
          title: "Could not check configuration",
          description: "Make sure the backend dependencies are installed.",
          variant: "destructive",
        })
      })
  }, [toast])

  return null
}
