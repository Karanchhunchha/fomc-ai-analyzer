"use client"

import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"

interface NumberTickerProps {
  value: number
  direction?: "up" | "down"
  delay?: number
  className?: string
}

export function NumberTicker({
  value,
  direction = "up",
  delay = 0,
  className,
}: NumberTickerProps) {
  const [displayValue, setDisplayValue] = useState(direction === "up" ? 0 : value)

  useEffect(() => {
    let startTimestamp: number | null = null
    const duration = 800 // 800ms animation duration
    const startVal = direction === "up" ? 0 : value
    const endVal = direction === "up" ? value : 0

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp
      const progress = Math.min((timestamp - startTimestamp) / duration, 1)
      const currentVal = Math.floor(progress * (endVal - startVal) + startVal)
      setDisplayValue(currentVal)
      if (progress < 1) {
        window.requestAnimationFrame(step)
      }
    }

    const timeoutId = setTimeout(() => {
      window.requestAnimationFrame(step)
    }, delay * 1000)

    return () => clearTimeout(timeoutId)
  }, [value, direction, delay])

  return (
    <span className={cn("inline-block tabular-nums", className)}>
      {displayValue}
    </span>
  )
}
