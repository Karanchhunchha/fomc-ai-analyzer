"use client"
import React, { useState } from "react"
import { FileText, Trash2, UploadCloud, BarChart3 } from "lucide-react"

export interface Document {
  id: string
  name: string
  chunks: number
  date: string
  hawkish_score?: number
  topics?: string[]
}

interface SidebarProps {
  documents: Document[]
  activeDocId: string | null
  onSelect: (id: string) => void
  onUploadClick: () => void
  onDeleteDoc: (id: string) => void
  queryCount: number
  queryLimit: number
  selectedTopics: string[]
  onToggleTopic: (topic: string) => void
}

export function Sidebar({
  documents,
  activeDocId,
  onSelect,
  onUploadClick,
  onDeleteDoc,
  queryCount,
  queryLimit,
  selectedTopics,
  onToggleTopic,
}: SidebarProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null)
  const rateLimitPercentage = Math.min(Math.round((queryCount / queryLimit) * 100), 100)

  // Extract all unique topics dynamically from the document inventory
  const uniqueTopics = React.useMemo(() => {
    const topicsSet = new Set<string>()
    documents.forEach((doc) => {
      if (doc.topics) {
        doc.topics.forEach((t) => {
          if (t && t !== "Unknown") {
            topicsSet.add(t)
          }
        })
      }
    })
    return Array.from(topicsSet).sort()
  }, [documents])

  // Filter listed documents by selected topics
  const filteredDocuments = React.useMemo(() => {
    if (selectedTopics.length === 0) return documents
    return documents.filter(
      (doc) => doc.topics && doc.topics.some((t) => selectedTopics.includes(t))
    )
  }, [documents, selectedTopics])

  return (
    <aside className="w-64 flex flex-col h-full bg-term-bg-panel border-r border-term-border select-none">
      {/* Title Header */}
      <div className="px-5 pt-4 pb-2 border-b border-term-border/40">
        <span className="text-[10px] font-mono tracking-widest text-term-text-muted uppercase">
          Document Inventory
        </span>
      </div>

      {/* Topic Filter Panel */}
      {uniqueTopics.length > 0 && (
        <div className="px-5 py-3 border-b border-term-border/40">
          <span className="text-[10px] font-mono tracking-widest text-term-text-muted uppercase block mb-2">
            Topic Filters
          </span>
          <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto pr-1">
            {uniqueTopics.map((topic) => {
              const isSelected = selectedTopics.includes(topic)
              return (
                <button
                  key={topic}
                  onClick={() => onToggleTopic(topic)}
                  className={`px-2 py-0.5 rounded-full text-[9px] font-mono border transition-all duration-150 cursor-pointer ${
                    isSelected
                      ? "bg-term-accent-blue/10 border-term-accent-blue/40 text-term-accent-blue font-semibold"
                      : "bg-term-bg-hover/20 border-term-border text-term-text-muted hover:text-term-text-secondary"
                  }`}
                >
                  {topic}
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Document Feed */}
      <div className="flex-1 overflow-y-auto py-2 px-3 space-y-1">
        {filteredDocuments.length === 0 ? (
          <div className="py-12 text-center px-4">
            <FileText className="h-6 w-6 text-term-text-muted mx-auto mb-2 opacity-50" />
            <p className="text-[11px] text-term-text-secondary font-medium">No files match</p>
            <p className="text-[10px] text-term-text-muted mt-1">Adjust filters or upload above</p>
          </div>
        ) : (
          filteredDocuments.map((doc) => {
            const isActive = doc.id === activeDocId
            const score = doc.hawkish_score ?? 0.0
            return (
              <div
                key={doc.id}
                onMouseEnter={() => setHoveredId(doc.id)}
                onMouseLeave={() => setHoveredId(null)}
                onClick={() => onSelect(doc.id)}
                className={`relative flex items-center justify-between p-2.5 rounded border transition-all duration-150 cursor-pointer ${
                  isActive
                    ? "bg-term-bg-card border-term-border shadow-sm text-term-text-primary"
                    : "border-transparent text-term-text-secondary hover:bg-term-bg-card/40 hover:text-term-text-primary"
                }`}
              >
                {/* Active indicator bar */}
                {isActive && (
                  <div className="absolute left-0 top-1.5 bottom-1.5 w-0.5 bg-term-accent-blue rounded-full" />
                )}

                {/* Info block */}
                <div className="flex items-start space-x-2.5 min-w-0">
                  {(() => {
                    const colorClass = score > 0.05
                      ? "text-term-hawkish-green bg-term-hawkish-green/5 border border-term-hawkish-green/20"
                      : score < -0.05
                        ? "text-term-dovish-red bg-term-dovish-red/5 border border-term-dovish-red/20"
                        : "text-term-accent-blue bg-term-accent-blue/5 border border-term-accent-blue/20"
                    
                    return (
                      <div className={`p-1.5 rounded shrink-0 ${isActive ? "bg-term-accent-blue/10 text-term-accent-blue border border-term-accent-blue/30" : colorClass}`}>
                        <FileText className="h-3.5 w-3.5" />
                      </div>
                    )
                  })()}
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold truncate leading-tight">
                      {doc.name.replace(/_/g, " ").replace(".pdf", "").replace(".txt", "")}
                    </p>
                    <p className="text-[9px] font-mono text-term-text-muted mt-0.5 font-medium">
                      {doc.chunks} chunks · {doc.date}
                    </p>
                  </div>
                </div>

                {/* Action Trash (Visible on hover) */}
                {hoveredId === doc.id && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteDoc(doc.id)
                    }}
                    className="p-1 rounded hover:bg-term-dovish-red/15 hover:text-term-dovish-red transition-all cursor-pointer text-term-text-muted shrink-0"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                )}
              </div>
            )
          })
        )}
      </div>

      {/* Footer controls & limiters */}
      <div className="border-t border-term-border p-4 space-y-4 bg-term-bg-panel/40">
        <button
          onClick={onUploadClick}
          className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded text-xs font-semibold text-term-text-secondary border border-dashed border-term-border hover:border-term-accent-blue/40 hover:text-term-text-primary bg-term-bg-card/20 hover:bg-term-bg-card/50 transition-all cursor-pointer duration-150"
        >
          <UploadCloud className="h-4 w-4 text-term-accent-blue shrink-0" />
          <span>Upload Document</span>
        </button>

        {/* Diagnostic Rate Limit Monitor */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center text-[10px] font-mono text-term-text-muted">
            <span className="flex items-center space-x-1">
              <BarChart3 className="h-3 w-3" />
              <span>RPM THROTTLE</span>
            </span>
            <span>{queryCount}/{queryLimit}</span>
          </div>
          <div className="h-1 bg-term-bg-hover rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                rateLimitPercentage > 85
                  ? "bg-term-dovish-red"
                  : rateLimitPercentage > 60
                    ? "bg-term-alert-amber"
                    : "bg-term-accent-blue"
              }`}
              style={{ width: `${rateLimitPercentage}%` }}
            />
          </div>
        </div>
      </div>
    </aside>
  )
}
