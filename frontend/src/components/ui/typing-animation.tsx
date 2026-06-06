"use client"

import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"

interface TypingAnimationProps {
  text: string
  duration?: number
  className?: string
}

export function TypingAnimation({
  text,
  duration = 15,
  className,
}: TypingAnimationProps) {
  const [displayedText, setDisplayedText] = useState("")

  useEffect(() => {
    let i = 0
    setDisplayedText("")
    const interval = setInterval(() => {
      if (i < text.length) {
        setDisplayedText((prev) => prev + text.charAt(i))
        i++
      } else {
        clearInterval(interval)
      }
    }, duration)

    return () => clearInterval(interval)
  }, [text, duration])

  return <span className={className}>{displayedText}</span>
}
