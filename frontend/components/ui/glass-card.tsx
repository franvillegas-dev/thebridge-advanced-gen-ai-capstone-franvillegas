import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cn } from "@/lib/utils"

interface GlassCardProps extends React.ComponentProps<"div"> {
  hover?: boolean
  asChild?: boolean
}

function GlassCard({ className, hover = false, asChild = false, children, ...props }: GlassCardProps) {
  const Comp = asChild ? Slot : "div"

  return (
    <Comp
      data-slot="glass-card"
      className={cn(
        "rounded-xl border border-border/40 bg-background/60 p-6 shadow-sm backdrop-blur-md",
        hover && "transition-shadow hover:shadow-md",
        className
      )}
      {...props}
    >
      {children}
    </Comp>
  )
}

export { GlassCard }
