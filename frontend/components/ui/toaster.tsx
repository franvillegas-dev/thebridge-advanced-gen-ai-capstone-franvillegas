"use client"

import { useToast } from "@/hooks/use-toast"

export function Toaster() {
  const { toasts, dismiss } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`rounded-lg border px-4 py-3 shadow-lg text-sm cursor-pointer animate-in slide-in-from-right ${
            t.variant === "destructive"
              ? "bg-destructive text-destructive-foreground border-destructive"
              : "bg-background text-foreground border-border"
          }`}
          onClick={() => dismiss(t.id)}
        >
          <strong className="block">{t.title}</strong>
          {t.description && <p className="text-xs mt-1 opacity-80">{t.description}</p>}
        </div>
      ))}
    </div>
  )
}
