"use client"
import React, { useState, useMemo } from "react"
import { Calendar, FileText, Activity } from "lucide-react"

export interface SentimentTimelineItem {
  date: string
  source: string
  hawk_score: number
  dove_score: number
  net_stance: number
}

interface SentimentTimelineProps {
  data: SentimentTimelineItem[]
}

export function SentimentTimeline({ data }: SentimentTimelineProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null)

  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => a.date.localeCompare(b.date))
  }, [data])

  const W = 700
  const H = 220
  const paddingX = 60
  const paddingY = 40
  const chartW = W - paddingX * 2
  const chartH = H - paddingY * 2

  const coordinates = useMemo(() => {
    if (sortedData.length === 0) return []
    return sortedData.map((item, idx) => {
      const x = sortedData.length > 1
        ? paddingX + (idx / (sortedData.length - 1)) * chartW
        : paddingX + chartW / 2

      // Map net stance -100 (dove) to bottom, +100 (hawk) to top
      const y = paddingY + chartH - ((item.net_stance + 100) / 200) * chartH
      return { x, y, item, idx }
    })
  }, [sortedData, chartW, chartH, paddingX, paddingY])

  const pathD = useMemo(() => {
    if (coordinates.length < 2) return ""
    return coordinates.map((pt, idx) => `${idx === 0 ? "M" : "L"} ${pt.x} ${pt.y}`).join(" ")
  }, [coordinates])

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6 border border-dashed border-term-border rounded-lg bg-term-bg-panel/20">
        <Activity className="h-6 w-6 text-term-text-muted mb-2 animate-pulse" />
        <p className="text-xs font-mono text-term-text-secondary">No Sentiment Data Available</p>
        <p className="text-[10px] text-term-text-muted mt-1">Ingest multiple meetings to generate stance timeline</p>
      </div>
    )
  }

  return (
    <div className="relative w-full h-full bg-term-bg-panel/40 border border-term-border rounded-lg p-4 select-none">
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center space-x-1.5">
          <Activity className="h-4 w-4 text-term-accent-blue" />
          <span className="text-[10px] font-mono font-bold tracking-widest text-term-text-secondary uppercase">
            POLICY STANCE DRIFT TIMELINE
          </span>
        </div>

        <div className="flex items-center space-x-4 text-[9px] font-mono text-term-text-muted">
          <span className="flex items-center space-x-1">
            <span className="h-1.5 w-1.5 rounded-full bg-term-hawkish-green" />
            <span>Hawkish (+)</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="h-1.5 w-1.5 rounded-full bg-term-dovish-red" />
            <span>Dovish (-)</span>
          </span>
        </div>
      </div>

      <div className="relative w-full flex justify-center">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto max-w-[700px] overflow-visible">
          {/* Y-axis Labels & Gridlines */}
          {[-100, -50, 0, 50, 100].map((level) => {
            const y = paddingY + chartH - ((level + 100) / 200) * chartH
            const isZero = level === 0
            return (
              <g key={level} className="opacity-60">
                <line
                  x1={paddingX}
                  y1={y}
                  x2={W - paddingX}
                  y2={y}
                  stroke={isZero ? "var(--term-accent-blue)" : "#1E1E2A"}
                  strokeDasharray={isZero ? "4 4" : "0"}
                  strokeWidth={isZero ? 1 : 0.5}
                />
                <text
                  x={paddingX - 10}
                  y={y + 3}
                  textAnchor="end"
                  fill="var(--term-text-muted)"
                  className="text-[8px] font-mono"
                >
                  {level > 0 ? `+${level}` : level}
                </text>
              </g>
            )
          })}

          {/* Area Fill */}
          {coordinates.length >= 2 && (
            <path
              d={`${pathD} L ${coordinates[coordinates.length - 1].x} ${paddingY + chartH / 2} L ${coordinates[0].x} ${paddingY + chartH / 2} Z`}
              fill="url(#timeline-area)"
              className="opacity-10"
            />
          )}

          {/* Gradients */}
          <defs>
            <linearGradient id="timeline-area" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--term-accent-blue)" stopOpacity="0.3" />
              <stop offset="100%" stopColor="var(--term-accent-blue)" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="timeline-line" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="var(--term-dovish-red)" />
              <stop offset="50%" stopColor="var(--term-accent-blue)" />
              <stop offset="100%" stopColor="var(--term-hawkish-green)" />
            </linearGradient>
          </defs>

          {/* Line Path */}
          {coordinates.length >= 2 && (
            <path
              d={pathD}
              fill="none"
              stroke="url(#timeline-line)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Intersect Dots */}
          {coordinates.map((pt) => {
            const isHovered = hoveredIdx === pt.idx
            const color = pt.item.net_stance >= 0 ? "var(--term-hawkish-green)" : "var(--term-dovish-red)"
            return (
              <g
                key={pt.idx}
                onMouseEnter={() => setHoveredIdx(pt.idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                className="cursor-pointer"
              >
                {isHovered && (
                  <circle
                    cx={pt.x}
                    cy={pt.y}
                    r="8"
                    fill={`${color}20`}
                    stroke={color}
                    strokeWidth="0.5"
                  />
                )}
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={isHovered ? "5.5" : "4"}
                  fill="var(--term-bg-deep)"
                  stroke={color}
                  strokeWidth={isHovered ? "2.5" : "1.5"}
                  className="transition-all duration-150"
                />
              </g>
            )
          })}
        </svg>

        {/* Floating Tooltip */}
        {hoveredIdx !== null && coordinates[hoveredIdx] && (
          <div
            className="absolute z-50 bg-term-bg-card border border-term-border rounded p-3 shadow-term-shadow pointer-events-none w-48 text-left animate-fade-in"
            style={{
              left: `${(coordinates[hoveredIdx].x / W) * 100}%`,
              top: `${(coordinates[hoveredIdx].y / H) * 100 - 45}%`,
              transform: "translate(-50%, -100%)",
            }}
          >
            <div className="space-y-1.5 text-[9px] font-mono">
              <div className="flex items-center space-x-1 text-term-text-secondary border-b border-term-border pb-1">
                <Calendar className="h-3 w-3 shrink-0" />
                <span>{coordinates[hoveredIdx].item.date}</span>
              </div>
              <div className="text-term-text-primary truncate">
                <FileText className="h-3 w-3 inline mr-1 text-term-accent-blue shrink-0" />
                <span>{coordinates[hoveredIdx].item.source}</span>
              </div>
              <div className="grid grid-cols-2 gap-x-2 pt-1 font-medium">
                <span className="text-term-text-muted">Net Stance:</span>
                <span className={`font-bold ${coordinates[hoveredIdx].item.net_stance >= 0 ? "text-term-hawkish-green" : "text-term-dovish-red"}`}>
                  {coordinates[hoveredIdx].item.net_stance > 0 ? "+" : ""}{coordinates[hoveredIdx].item.net_stance}
                </span>
                <span className="text-term-text-muted">Hawk/Dove:</span>
                <span className="text-term-text-primary">
                  {coordinates[hoveredIdx].item.hawk_score}/{coordinates[hoveredIdx].item.dove_score}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
