"use client"
import React, { useState, useEffect } from "react"
import { listDocuments, queryDocumentsStream, getSentimentTimeline, SentimentTimelineItem } from "@/lib/api"
import { Topbar } from "@/components/Topbar"
import { ArrowLeft, GitCompare, Sparkles, Scale, ShieldAlert, Cpu } from "lucide-react"
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

export default function ComparePage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [timelineData, setTimelineData] = useState<SentimentTimelineItem[]>([])
  const [healthData, setHealthData] = useState<any>(null)
  
  const [docAId, setDocAId] = useState<string>("")
  const [docBId, setDocBId] = useState<string>("")
  
  const [comparisonAnswer, setComparisonAnswer] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchInitialData()
  }, [])

  const fetchInitialData = async () => {
    try {
      const docs = await listDocuments()
      const mappedDocs = docs.map((d: any) => ({
        id: d.id,
        name: d.id,
        chunks: d.chunks,
        date: d.date || "Unknown"
      }))
      setDocuments(mappedDocs)
      
      if (mappedDocs.length >= 2) {
        setDocAId(mappedDocs[0].id)
        setDocBId(mappedDocs[1].id)
      } else if (mappedDocs.length === 1) {
        setDocAId(mappedDocs[0].id)
      }
      
      const tl = await getSentimentTimeline()
      setTimelineData(tl)

      const hRes = await fetch("/api/health")
      if (hRes.ok) {
        setHealthData(await hRes.json())
      }
    } catch (e) {
      console.error("Failed to load compare workspace data", e)
    }
  }

  // Find scores in timeline data
  const docAScores = timelineData.find(t => t.source === docAId)
  const docBScores = timelineData.find(t => t.source === docBId)

  const handleCompare = async () => {
    if (!docAId || !docBId || docAId === docBId || isLoading) return
    setIsLoading(true)
    setError(null)
    setComparisonAnswer("")

    const docAName = docAId.replace(/_/g, " ").replace(".pdf", "").replace(".txt", "")
    const docBName = docBId.replace(/_/g, " ").replace(".pdf", "").replace(".txt", "")
    
    const query = `Compare the policy decisions, economic outlook, inflation concerns, and voting outcomes between the FOMC meeting on ${docAScores?.date || docAName} and the meeting on ${docBScores?.date || docBName} based on the retrieved transcripts. Provide a summary highlighting the differences and shifts in hawkish/dovish stances.`

    let collectedAnswer = ""
    try {
      await queryDocumentsStream(query, 5, "auto", "compare-session", {
        onChunk: (chunk: string) => {
          collectedAnswer += chunk
          setComparisonAnswer(collectedAnswer)
        },
        onDone: () => {
          setIsLoading(false)
        },
        onError: (err) => {
          console.error("Comparison stream error:", err)
          setError(err.message || "Failed to run comparative analysis. Please try again.")
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
              Policy Comparison Panel
            </h1>
            <p className="text-xs text-term-text-secondary">
              Analyze stance shifts, rate policy drift, and sentiment metrics side-by-side.
            </p>
          </div>
        </div>

        {documents.length < 2 ? (
          <div className="text-center py-20 bg-term-bg-panel border border-term-border rounded-lg shadow-term-shadow p-6">
            <GitCompare className="h-10 w-10 text-term-text-muted mx-auto mb-3 opacity-55 animate-pulse" />
            <h3 className="text-sm font-semibold text-term-text-primary">Insufficient Documents</h3>
            <p className="text-xs text-term-text-muted mt-1 max-w-xs mx-auto">
              You need at least 2 documents in the database to run comparative policy diagnostics. Go to the Document Index to upload files.
            </p>
            <div className="mt-4">
              <Link href="/documents">
                <ShimmerButton
                  shimmerColor="#3B82F6"
                  background="rgba(21, 21, 31, 1)"
                  borderRadius="6px"
                  className="h-8 px-4 text-xs font-semibold text-term-accent-blue border border-term-accent-blue/30 cursor-pointer"
                >
                  Manage Documents
                </ShimmerButton>
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Left: Document Selectors & Sentiment Gauges */}
            <div className="md:col-span-5 space-y-6 select-none">
              <div className="bg-term-bg-panel border border-term-border rounded-lg p-5 space-y-4">
                <span className="text-[10px] font-mono tracking-widest text-term-text-muted uppercase">
                  SELECTOR DECK
                </span>
                
                {/* Selectors */}
                <div className="space-y-3">
                  <div className="space-y-1">
                    <label className="text-[10px] font-mono text-term-text-secondary">DOCUMENT A</label>
                    <select
                      value={docAId}
                      onChange={(e) => setDocAId(e.target.value)}
                      className="w-full bg-term-bg-card border border-term-border rounded px-3 py-2 text-xs text-term-text-primary focus:outline-none focus:border-term-accent-blue cursor-pointer"
                    >
                      {documents.map(d => (
                        <option key={d.id} value={d.id}>{d.name}</option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[10px] font-mono text-term-text-secondary">DOCUMENT B</label>
                    <select
                      value={docBId}
                      onChange={(e) => setDocBId(e.target.value)}
                      className="w-full bg-term-bg-card border border-term-border rounded px-3 py-2 text-xs text-term-text-primary focus:outline-none focus:border-term-accent-blue cursor-pointer"
                    >
                      {documents.map(d => (
                        <option key={d.id} value={d.id} disabled={d.id === docAId}>{d.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="pt-2">
                  <ShimmerButton
                    onClick={handleCompare}
                    disabled={isLoading || !docAId || !docBId || docAId === docBId}
                    shimmerColor="#3B82F6"
                    background="rgba(21, 21, 31, 1)"
                    borderRadius="6px"
                    className="w-full h-9 text-xs font-semibold text-term-accent-blue border border-term-accent-blue/30 cursor-pointer disabled:opacity-40"
                  >
                    <div className="flex items-center justify-center space-x-1.5">
                      <Sparkles className="h-4 w-4 shrink-0" />
                      <span>{isLoading ? "Comparing..." : "Generate Analysis"}</span>
                    </div>
                  </ShimmerButton>
                </div>
              </div>

              {/* Side-by-Side Sentiment Readout */}
              <div className="bg-term-bg-panel border border-term-border rounded-lg p-5 space-y-4">
                <span className="text-[10px] font-mono tracking-widest text-term-text-muted uppercase">
                  SENTIMENT SCORE COMPARE
                </span>

                <div className="grid grid-cols-2 gap-4">
                  {/* Doc A scores */}
                  <div className="border border-term-border rounded p-3 space-y-2 bg-term-bg-deep/40">
                    <p className="text-[10px] font-semibold text-term-text-secondary truncate">Doc A Scores</p>
                    {docAScores ? (
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs font-mono">
                          <span className="text-term-hawkish-green">Hawk:</span>
                          <span className="text-term-text-primary font-bold">{docAScores.hawk_score}%</span>
                        </div>
                        <div className="flex justify-between text-xs font-mono">
                          <span className="text-term-dovish-red">Dove:</span>
                          <span className="text-term-text-primary font-bold">{docAScores.dove_score}%</span>
                        </div>
                        <div className="flex justify-between text-xs font-mono border-t border-term-border pt-1 mt-1 font-bold">
                          <span className="text-term-text-secondary">Net:</span>
                          <span className={docAScores.net_stance >= 0 ? "text-term-hawkish-green" : "text-term-dovish-red"}>
                            {docAScores.net_stance > 0 ? "+" : ""}{docAScores.net_stance}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-[9px] text-term-text-muted italic">Unavailable</p>
                    )}
                  </div>

                  {/* Doc B scores */}
                  <div className="border border-term-border rounded p-3 space-y-2 bg-term-bg-deep/40">
                    <p className="text-[10px] font-semibold text-term-text-secondary truncate">Doc B Scores</p>
                    {docBScores ? (
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs font-mono">
                          <span className="text-term-hawkish-green">Hawk:</span>
                          <span className="text-term-text-primary font-bold">{docBScores.hawk_score}%</span>
                        </div>
                        <div className="flex justify-between text-xs font-mono">
                          <span className="text-term-dovish-red">Dove:</span>
                          <span className="text-term-text-primary font-bold">{docBScores.dove_score}%</span>
                        </div>
                        <div className="flex justify-between text-xs font-mono border-t border-term-border pt-1 mt-1 font-bold">
                          <span className="text-term-text-secondary">Net:</span>
                          <span className={docBScores.net_stance >= 0 ? "text-term-hawkish-green" : "text-term-dovish-red"}>
                            {docBScores.net_stance > 0 ? "+" : ""}{docBScores.net_stance}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-[9px] text-term-text-muted italic">Unavailable</p>
                    )}
                  </div>
                </div>

                {/* Macro summary card */}
                {docAScores && docBScores && (
                  <div className="border border-term-border p-3 rounded text-[10px] leading-relaxed text-term-text-secondary bg-term-bg-card/40">
                    <Scale className="h-3.5 w-3.5 inline mr-1 text-term-accent-blue align-middle shrink-0" />
                    <span>
                      Stance shifted by{" "}
                      <strong className="text-term-text-primary font-bold">{Math.abs(docBScores.net_stance - docAScores.net_stance)} points</strong>.{" "}
                      {docBScores.net_stance > docAScores.net_stance 
                        ? "Policy direction became more HAWKISH." 
                        : "Policy direction became more DOVISH."}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Right: Comparative Analysis Output */}
            <div className="md:col-span-7">
              <div className="bg-term-bg-panel border border-term-border rounded-lg h-[460px] flex flex-col overflow-hidden relative shadow-term-shadow">
                {isLoading && (
                  <BorderBeam size={400} duration={3} colorFrom="var(--term-accent-blue)" colorTo="var(--term-hawkish-green)" />
                )}

                <div className="px-5 py-4 border-b border-term-border flex items-center justify-between select-none">
                  <div className="flex items-center space-x-2">
                    <Cpu className="h-4 w-4 text-term-accent-blue" />
                    <span className="text-[10px] font-mono tracking-widest text-term-text-secondary uppercase">
                      Comparative Analysis Output
                    </span>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-5 text-sm leading-relaxed text-term-text-primary font-body whitespace-pre-wrap">
                  {error && (
                    <div className="bg-term-dovish-red/10 border border-term-dovish-red/20 p-3 rounded flex items-center space-x-2 text-xs text-term-dovish-red mb-4">
                      <ShieldAlert className="h-4 w-4 shrink-0" />
                      <span>{error}</span>
                    </div>
                  )}

                  {comparisonAnswer ? (
                    isLoading ? (
                      <TypingAnimation text={comparisonAnswer} duration={10} />
                    ) : (
                      comparisonAnswer
                    )
                  ) : (
                    <p className="text-xs text-term-text-muted italic select-none text-center py-24">
                      Select two files on the left and click "Generate Analysis" to run the comparison.
                    </p>
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
