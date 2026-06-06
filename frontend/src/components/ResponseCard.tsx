"use client"
import React from "react"
import { BorderBeam } from "@/components/ui/border-beam"
import { TypingAnimation } from "@/components/ui/typing-animation"
import { Clock, CheckCircle2, FileText } from "lucide-react"

export interface Excerpt {
  num: number
  page: number
  text: string
  similarity: number
  source: string
}

interface ResponseCardProps {
  query: string
  answer: string
  excerpts: Excerpt[]
  confidence: "HIGH" | "MEDIUM" | "LOW"
  metadata: {
    responseMs: number
    cacheHit: boolean
    chunksSearched: number
    meetingDate: string
  }
  isStreaming?: boolean
  onExcerptClick?: (idx: number) => void
}

export function ResponseCard({
  query,
  answer,
  excerpts,
  confidence,
  metadata,
  isStreaming,
  onExcerptClick,
}: ResponseCardProps) {
  const confidenceStyles = {
    HIGH: "bg-term-hawkish-green/5 border-term-hawkish-green/20 text-term-hawkish-green",
    MEDIUM: "bg-term-alert-amber/5 border-term-alert-amber/20 text-term-alert-amber",
    LOW: "bg-term-dovish-red/5 border-term-dovish-red/20 text-term-dovish-red",
  }

  // Parse inline citations like [1] to render interactive terminal tokens
  const formatText = (rawText: string) => {
    if (!rawText) return ""
    const citeRegex = /(\[\d+\])/g
    const parts = rawText.split(citeRegex)
    return parts.map((part, idx) => {
      if (part.startsWith("[") && part.endsWith("]")) {
        const num = parseInt(part.replace(/[\[\]]/g, ""))
        return (
          <button
            key={idx}
            onClick={() => onExcerptClick && onExcerptClick(num - 1)}
            className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-term-accent-blue/10 hover:bg-term-accent-blue/20 border border-term-accent-blue/20 text-term-accent-blue mx-0.5 transition-colors cursor-pointer"
          >
            {part}
          </button>
        )
      }
      return <span key={idx}>{part}</span>
    })
  }

  return (
    <div className="flex flex-col space-y-4 max-w-3xl mx-auto w-full animate-slide-up">
      {/* User Question */}
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-term-bg-panel border border-term-border rounded-lg rounded-tr-none px-4 py-3 shadow-md">
          <p className="text-sm font-body text-term-text-primary leading-relaxed">
            {query}
          </p>
        </div>
      </div>

      {/* AI Grounded Synthesis Panel */}
      <div className="relative bg-term-bg-card border border-term-border rounded-lg shadow-term-shadow overflow-hidden">
        {/* Border beam during generation stream */}
        {isStreaming && (
          <BorderBeam size={350} duration={3} colorFrom="var(--term-accent-blue)" colorTo="var(--term-hawkish-green)" />
        )}

        <div className="p-5">
          {/* Header diagnostic line */}
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-term-border">
            <div className="flex items-center space-x-2">
              <div className="h-5 w-5 rounded-full bg-term-accent-blue/15 border border-term-accent-blue/35 flex items-center justify-center font-mono text-[9px] text-term-accent-blue">
                AI
              </div>
              <span className="text-[10px] font-mono text-term-text-secondary tracking-widest uppercase">
                Grounded Synthesis · {metadata.meetingDate}
              </span>
            </div>

            <div className="flex items-center space-x-2 select-none">
              <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border ${confidenceStyles[confidence]}`}>
                CONFIDENCE: {confidence}
              </span>
            </div>
          </div>

          {/* Response Text */}
          <div className="text-sm font-body text-term-text-primary leading-relaxed whitespace-pre-wrap">
            {isStreaming ? (
              <TypingAnimation text={answer} duration={15} />
            ) : (
              formatText(answer)
            )}
          </div>

          {/* Diagnostic chips */}
          <div className="flex items-center space-x-2 mt-4 pt-3 border-t border-term-border/40 select-none">
            <span className="flex items-center space-x-1 text-[9px] font-mono text-term-text-muted bg-term-bg-deep border border-term-border px-2 py-0.5 rounded font-medium">
              <Clock className="h-3 w-3" />
              <span>{metadata.responseMs}ms</span>
            </span>
            <span className="flex items-center space-x-1 text-[9px] font-mono text-term-text-muted bg-term-bg-deep border border-term-border px-2 py-0.5 rounded font-medium">
              <CheckCircle2 className="h-3 w-3" />
              <span>{metadata.cacheHit ? "CACHE HIT" : "FRESH RUN"}</span>
            </span>
            <span className="flex items-center space-x-1 text-[9px] font-mono text-term-text-muted bg-term-bg-deep border border-term-border px-2 py-0.5 rounded font-medium">
              <FileText className="h-3 w-3" />
              <span>{metadata.chunksSearched} CHUNKS</span>
            </span>
          </div>
        </div>

        {/* Integrated evidence card dock */}
        {excerpts.length > 0 && (
          <div className="border-t border-term-border grid grid-cols-3 divide-x divide-term-border bg-term-bg-deep/40 select-none">
            {excerpts.map((exc) => (
              <div
                key={exc.num}
                onClick={() => onExcerptClick && onExcerptClick(exc.num - 1)}
                className="p-3.5 hover:bg-term-bg-hover/30 transition-colors cursor-pointer group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono font-bold text-term-accent-blue">
                    [{exc.num}] Page {exc.page}
                  </span>
                  <span className="text-[9px] font-mono text-term-text-muted bg-term-bg-deep px-1.5 py-0.5 rounded border border-term-border font-medium">
                    {Math.round(exc.similarity * 100)}% Match
                  </span>
                </div>
                <p className="text-[11px] text-term-text-secondary leading-relaxed line-clamp-3 group-hover:text-term-text-primary transition-colors">
                  {exc.text}
                </p>
                <p className="text-[9px] font-mono text-term-text-muted truncate mt-2 font-medium">
                  {exc.source}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
