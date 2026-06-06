"use client"
import React from "react"
import { Database, FileCode, ChevronRight } from "lucide-react"

export interface EvidenceChunk {
  id: string
  page: number
  text: string
  similarity: number
  source: string
  meetingDate: string
  isHighlighted?: boolean
}

interface EvidencePanelProps {
  chunks: EvidenceChunk[]
  highlightedIndex: number | null
}

export function EvidencePanel({ chunks, highlightedIndex }: EvidencePanelProps) {
  return (
    <aside className="w-80 flex flex-col h-full bg-term-bg-panel border-l border-term-border select-none">
      {/* Title */}
      <div className="px-5 py-4 border-b border-term-border flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Database className="h-4 w-4 text-term-accent-blue" />
          <span className="text-[10px] font-mono tracking-widest text-term-text-secondary uppercase">
            Retrieved Evidence Cards
          </span>
        </div>
        <span className="text-[9px] font-mono text-term-text-muted">{chunks.length} active</span>
      </div>

      {/* Cards List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {chunks.length === 0 ? (
          <div className="h-full flex flex-col justify-center items-center text-center py-12 px-4 opacity-50">
            <FileCode className="h-6 w-6 text-term-text-muted mb-2" />
            <p className="text-[11px] text-term-text-secondary font-medium">No evidence loaded</p>
            <p className="text-[9px] text-term-text-muted mt-1">Submit a query to inspect source excerpts</p>
          </div>
        ) : (
          chunks.map((chk, idx) => {
            const isHighlighted = highlightedIndex === idx
            const scorePercent = Math.round(chk.similarity * 100)
            return (
              <div
                id={`source-card-${idx}`}
                key={chk.id || idx}
                className={`rounded border p-3.5 transition-all duration-200 ${
                  isHighlighted 
                    ? "bg-term-accent-blue/10 border-term-accent-blue/40 shadow-glow-blue" 
                    : "bg-term-bg-card border-term-border hover:border-term-border-hover"
                }`}
              >
                {/* Header info */}
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono font-bold text-term-accent-blue flex items-center">
                    <ChevronRight className="h-3.5 w-3.5 inline text-term-accent-blue mr-0.5" />
                    Excerpt {idx + 1}
                  </span>
                  <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded ${
                    chk.similarity >= 0.70 
                      ? "text-term-hawkish-green bg-term-hawkish-green/5 border border-term-hawkish-green/10" 
                      : "text-term-text-secondary bg-term-bg-hover"
                  }`}>
                    {scorePercent}% Match
                  </span>
                </div>

                {/* Excerpt context text */}
                <p className="text-[11px] text-term-text-secondary leading-relaxed font-body">
                  {chk.text}
                </p>

                {/* Footer metadata */}
                <div className="mt-3 pt-2.5 border-t border-term-border/40 flex items-center justify-between text-[9px] font-mono text-term-text-muted font-medium">
                  <span className="truncate max-w-[120px]">{chk.source}</span>
                  <span>Page {chk.page} · {chk.meetingDate}</span>
                </div>
              </div>
            )
          })
        )}
      </div>
    </aside>
  )
}
