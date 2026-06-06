"use client"
import React, { useState, useRef, KeyboardEvent } from "react"
import { ShimmerButton } from "@/components/ui/shimmer-button"
import { Sparkles, CornerDownLeft } from "lucide-react"

interface QueryInputBarProps {
  onQuerySubmit: (query: string) => void
  isLoading: boolean
  disabled: boolean
}

export function QueryInputBar({ onQuerySubmit, isLoading, disabled }: QueryInputBarProps) {
  const [value, setValue] = useState("")
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || isLoading || disabled) return
    onQuerySubmit(trimmed)
    setValue("")
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t border-term-border bg-term-bg-panel/60 backdrop-blur-md p-4">
      <div className="max-w-3xl mx-auto">
        <div className="relative flex items-end bg-term-bg-card border border-term-border rounded-lg p-2 focus-within:border-term-border-hover transition-colors shadow-lg">
          <textarea
            ref={inputRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Query interest rate paths, hawkish/dovish pivots, or asset purchases..."
            rows={1}
            className="flex-1 bg-transparent text-sm font-body text-term-text-primary placeholder:text-term-text-muted resize-none outline-none max-h-36 py-1.5 px-2.5 leading-relaxed focus:ring-0"
            style={{ fieldSizing: "content" } as any}
          />

          <div className="flex items-center space-x-2 shrink-0">
            {/* Shimmer Button from 21st.dev */}
            <ShimmerButton
              onClick={handleSend}
              disabled={isLoading || disabled || !value.trim()}
              shimmerColor="#3B82F6"
              background="rgba(21, 21, 31, 1)"
              borderRadius="6px"
              className="h-8 px-4 text-xs font-semibold text-term-accent-blue border border-term-accent-blue/30 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
            >
              <div className="flex items-center space-x-1.5">
                {isLoading ? (
                  <span>Analyzing...</span>
                ) : (
                  <>
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Run Query</span>
                  </>
                )}
              </div>
            </ShimmerButton>
          </div>
        </div>

        <div className="flex justify-between items-center mt-2 px-2 text-[10px] font-mono text-term-text-muted select-none">
          <span className="flex items-center space-x-1">
            <CornerDownLeft className="h-3 w-3" />
            <span>Press Enter to send (Shift+Enter for newline)</span>
          </span>
          <span>Factual Grounding: Active</span>
        </div>
      </div>
    </div>
  )
}
