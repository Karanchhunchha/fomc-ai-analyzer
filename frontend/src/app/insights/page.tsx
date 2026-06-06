"use client"
import React, { useState, useEffect } from "react"
import { listDocuments, queryDocumentsStream, getSentimentTimeline, SentimentTimelineItem } from "@/lib/api"
import { Topbar } from "@/components/Topbar"
import { SentimentTimeline } from "@/components/SentimentTimeline"
import { ArrowLeft, TrendingUp, Sparkles, BookOpen, AlertCircle, Cpu } from "lucide-react"
import Link from "next/link"
import { ShimmerButton } from "@/components/ui/shimmer-button"
import { TypingAnimation } from "@/components/ui/typing-animation"
import { BorderBeam } from "@/components/ui/border-beam"

interface Document {
  id: string
  name: string
  chunks: number
  date: string
}

export default function InsightsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [timeline, setTimeline] = useState<SentimentTimelineItem[]>([])
  const [healthData, setHealthData] = useState<any>(null)
  
  const [selectedTopic, setSelectedTopic] = useState<string>("inflation")
  const [insightText, setInsightText] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchInitialData()
  }, [])

  const fetchInitialData = async () => {
    try {
      const docs = await listDocuments()
      setDocuments(docs.map((d: any) => ({
        id: d.id,
        name: d.id,
        chunks: d.chunks,
        date: d.date || "Unknown"
      })))
      
      const tl = await getSentimentTimeline()
      setTimeline(tl)

      const hRes = await fetch("/api/health")
      if (hRes.ok) {
        setHealthData(await hRes.json())
      }
    } catch (e) {
      console.error("Failed to load insights workspace data", e)
    }
  }

  const handleFetchInsights = async (topic: string) => {
    setSelectedTopic(topic)
    setIsLoading(true)
    setError(null)
    setInsightText("")

    const topicPrompts: Record<string, string> = {
      inflation: "Extract all key discussions, projections, metrics, and risk assessments regarding INFLATION (PCE, CPI, core inflation) across the available FOMC minutes. Provide a detailed summary.",
      labor: "Extract all discussions, unemployment rates, payroll indicators, and hiring trends regarding the LABOR MARKET and EMPLOYMENT across the available FOMC minutes. Provide a detailed summary.",
      interest: "Extract all mentions of the interest rate policy decisions, federal funds rate target ranges, discount rate adjustments, and future path trajectories across the available FOMC minutes.",
      global: "Extract all discussions on international economic developments, global trade policies, currency movements, tariffs, and geopolitical risks across the available FOMC minutes."
    }

    const query = topicPrompts[topic] || topicPrompts.inflation
    let collectedAnswer = ""

    try {
      await queryDocumentsStream(query, 5, "auto", "insights-session", {
        onChunk: (chunk: string) => {
          collectedAnswer += chunk
          setInsightText(collectedAnswer)
        },
        onDone: () => {
          setIsLoading(false)
        },
        onError: (err) => {
          console.error("Insights stream error:", err)
          setError(err.message || "Failed to generate macroeconomic insight. Please try again.")
          setIsLoading(false)
        }
      })
    } catch (e) {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-term-bg-deep text-term-text-primary overflow-hidden">
      <Topbar
        docCount={healthData?.indexed_documents || documents.length}
        cacheCount={healthData?.cache_entries || 0}
        isBackendLive={!!healthData}
        model={healthData?.model || "gemini-2.5-flash"}
      />

      <div className="flex-1 overflow-y-auto p-8 max-w-5xl mx-auto w-full space-y-6">
        {/* Navigation & Header */}
        <div className="flex items-center space-x-3 pb-4 border-b border-term-border select-none">
          <Link
            href="/workspace"
            className="p-2 rounded bg-term-bg-panel hover:bg-term-bg-card border border-term-border text-term-text-secondary hover:text-term-text-primary transition-all cursor-pointer"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="font-display text-xl font-bold tracking-tight text-term-text-primary">
              Macroeconomic Insights Terminal
            </h1>
            <p className="text-xs text-term-text-secondary">
              Analyze macro trends, policy drift timelines, and index metrics across meetings.
            </p>
          </div>
        </div>

        {/* Stance timeline trend */}
        <div className="space-y-2">
          <span className="text-[10px] font-mono tracking-widest text-term-text-muted uppercase select-none">
            CHRONOLOGICAL STANCE TRENDS
          </span>
          <div className="h-64">
            <SentimentTimeline data={timeline} />
          </div>
        </div>

        {/* Bottom Panel: Analytical Pivots */}
        {documents.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Left: Pivot Topics Selectors */}
            <div className="md:col-span-4 space-y-3 select-none">
              <span className="text-[10px] font-mono tracking-widest text-term-text-muted uppercase">
                ANALYSIS PIVOTS
              </span>

              {[
                { id: "inflation", label: "Inflation Diagnostics", desc: "PCE & CPI core indexes" },
                { id: "labor", label: "Labor & Employment", desc: "Unemployment, payrolls, & hiring" },
                { id: "interest", label: "Interest Rate Stance", desc: "Target ranges & future projections" },
                { id: "global", label: "Global Trade & Risks", desc: "Tariffs & international spillovers" }
              ].map((pivot) => (
                <div
                  key={pivot.id}
                  onClick={() => !isLoading && handleFetchInsights(pivot.id)}
                  className={`p-3.5 rounded border transition-all duration-150 cursor-pointer ${
                    selectedTopic === pivot.id
                      ? "bg-term-bg-card border-term-accent-blue/30 text-term-text-primary shadow-sm"
                      : "bg-term-bg-panel/40 border-term-border text-term-text-secondary hover:bg-term-bg-card hover:text-term-text-primary"
                  } ${isLoading ? "pointer-events-none opacity-60" : ""}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold">{pivot.label}</span>
                    <TrendingUp className={`h-3.5 w-3.5 ${selectedTopic === pivot.id ? "text-term-accent-blue" : "text-term-text-muted"}`} />
                  </div>
                  <p className="text-[10px] text-term-text-muted mt-1 leading-normal font-medium">{pivot.desc}</p>
                </div>
              ))}
            </div>

            {/* Right: Insights output */}
            <div className="md:col-span-8">
              <div className="bg-term-bg-panel border border-term-border rounded-lg h-[340px] flex flex-col overflow-hidden relative shadow-term-shadow">
                {isLoading && (
                  <BorderBeam size={400} duration={3} colorFrom="var(--term-accent-blue)" colorTo="var(--term-hawkish-green)" />
                )}

                <div className="px-5 py-4 border-b border-term-border flex items-center justify-between select-none">
                  <div className="flex items-center space-x-2">
                    <Cpu className="h-4 w-4 text-term-accent-blue" />
                    <span className="text-[10px] font-mono tracking-widest text-term-text-secondary uppercase">
                      Macro Analyst Synthesis
                    </span>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-5 text-sm leading-relaxed text-term-text-primary font-body whitespace-pre-wrap">
                  {error && (
                    <div className="bg-term-dovish-red/10 border border-term-dovish-red/20 p-3 rounded flex items-center space-x-2 text-xs text-term-dovish-red mb-4">
                      <AlertCircle className="h-4 w-4 shrink-0" />
                      <span>{error}</span>
                    </div>
                  )}

                  {insightText ? (
                    isLoading ? (
                      <TypingAnimation text={insightText} duration={10} />
                    ) : (
                      insightText
                    )
                  ) : (
                    <div className="text-center py-20 select-none">
                      <BookOpen className="h-8 w-8 text-term-text-muted mx-auto mb-2 opacity-50" />
                      <p className="text-xs text-term-text-muted italic">
                        Select an analytical pivot on the left to generate model synthesis.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
