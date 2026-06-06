"use client"

import React from "react"
import { cn } from "@/lib/utils"

interface SpotlightProps {
  className?: string
  fill?: string
}

export function Spotlight({
  className,
  fill = "rgba(59, 130, 246, 0.15)",
}: SpotlightProps) {
  return (
    <div
      className={cn(
        "pointer-events-none absolute h-[500px] w-[500px] rounded-full blur-[120px] opacity-75",
        className
      )}
      style={{
        background: `radial-gradient(circle, ${fill} 0%, transparent 70%)`,
      }}
    />
  )
}
