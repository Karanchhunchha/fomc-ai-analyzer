"use client"
import React, { useState, useEffect, useRef } from "react"
import { Topbar } from "@/components/Topbar"
import { Sidebar, Document } from "@/components/Sidebar"
import { QueryInputBar } from "@/components/QueryInputBar"
import { ResponseCard, Excerpt } from "@/components/ResponseCard"
import { EvidencePanel, EvidenceChunk } from "@/components/EvidencePanel"
import { SentimentTimeline, SentimentTimelineItem } from "@/components/SentimentTimeline"
import { DotPattern } from "@/components/ui/dot-pattern"
import { Spotlight } from "@/components/ui/spotlight"
import { listDocuments, deleteDocument, uploadDocument, getSentimentTimeline, queryDocumentsStream } from "@/lib/api"
import { AlertCircle } from "lucide-react"

interface ChatMessage {
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
}

export default function WorkspacePage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [activeDocId, setActiveDocId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [evidence, setEvidence] = useState<EvidenceChunk[]>([])
  const [timeline, setTimeline] = useState<SentimentTimelineItem[]>([])
  const [healthData, setHealthData] = useState<any>(null)
  
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [queryCount, setQueryCount] = useState(0)
  const [highlightedExcerptIdx, setHighlightedExcerptIdx] = useState<number | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchInitialData()
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleToggleTopic = (topic: string) => {
    setSelectedTopics(prev =>
      prev.includes(topic) ? prev.filter(t => t !== topic) : [...prev, topic]
    )
  }

  const fetchInitialData = async () => {
    try {
      const docs = await listDocuments()
      setDocuments(docs.map((d: any) => ({
        id: d.id,
        name: d.id,
        chunks: d.chunks,
        date: d.date || "Unknown",
        hawkish_score: d.hawkish_score,
        topics: d.topics
      })))
      
      const tl = await getSentimentTimeline()
      setTimeline(tl)

      // Fetch health data for stats
      const hRes = await fetch("/api/health")
      if (hRes.ok) {
        const hData = await hRes.json()
        setHealthData(hData)
      }
    } catch (e) {
      console.error("Failed to load diagnostic workspace data", e)
    }
  }

  const handleQuery = async (query: string) => {
    if (!query.trim() || isLoading) return
    setIsLoading(true)
    setHighlightedExcerptIdx(null)
    setQueryCount(prev => prev + 1)

    const initialMsg: ChatMessage = {
      query,
      answer: "",
      excerpts: [],
      confidence: "MEDIUM",
      metadata: {
        responseMs: 0,
        cacheHit: false,
        chunksSearched: 0,
        meetingDate: "..."
      },
      isStreaming: true
    }

    setMessages(prev => [...prev, initialMsg])

    const start = Date.now()
    let collectedAnswer = ""
    let collectedSources: any[] = []

    try {
      await queryDocumentsStream(query, 5, "auto", "default-session", {
        onChunk: (chunk: string) => {
          collectedAnswer += chunk
          setMessages(prev => prev.map((msg, idx) => 
            idx === prev.length - 1 ? { ...msg, answer: collectedAnswer } : msg
          ))
        },
        onMetadata: (meta: any) => {
          collectedSources = meta.sources || []
          const mappedExcerpts: Excerpt[] = collectedSources.map((s: any, idx: number) => ({
            num: idx + 1,
            page: s.page_number || 1,
            text: s.chunk_text || s.text || "",
            similarity: meta.similarity_scores?.[idx] || 0.80,
            source: s.source_document || "Unknown"
          }))

          const mappedEvidence: EvidenceChunk[] = collectedSources.map((s: any, idx: number) => ({
            id: s.chunk_id || String(idx),
            page: s.page_number || 1,
            text: s.chunk_text || s.text || "",
            similarity: meta.similarity_scores?.[idx] || 0.80,
            source: s.source_document || "Unknown",
            meetingDate: s.meeting_date || "Unknown"
          }))

          setEvidence(mappedEvidence)
          setMessages(prev => prev.map((msg, idx) => 
            idx === prev.length - 1 
              ? { 
                  ...msg, 
                  excerpts: mappedExcerpts,
                  confidence: meta.confidence >= 0.7 ? "HIGH" : meta.confidence >= 0.5 ? "MEDIUM" : "LOW",
                  metadata: {
                    responseMs: Date.now() - start,
                    cacheHit: meta.cache_hit || false,
                    chunksSearched: meta.sources?.length || 0,
                    meetingDate: (() => {
                      const topSource = meta.sources?.[0];
                      const topChunkMeetingDate = topSource?.meeting_date;
                      if (topChunkMeetingDate && topChunkMeetingDate !== "Unknown") {
                        // Format full date to "Jan 2026" style
                        const dateMatch = topChunkMeetingDate.match(/(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+,\s+(\d{4})/);
                        if (dateMatch) {
                          const month = dateMatch[1].substring(0, 3);
                          const year = dateMatch[2];
                          return `${month} ${year}`;
                        }
                        return topChunkMeetingDate;
                      }
                      // Fallback to source document name
                      const sourceDoc = topSource?.source_document;
                      if (typeof sourceDoc === "string" && sourceDoc) {
                        return sourceDoc.replace(/_/g, ' ').replace(/\.(pdf|htm|txt)$/i, '');
                      }
                      return "Unknown";
                    })()
                  }
                } 
              : msg
          ))
        },
        onDone: () => {
          setMessages(prev => prev.map((msg, idx) => 
            idx === prev.length - 1 ? { ...msg, isStreaming: false } : msg
          ))
          setIsLoading(false)
          fetchInitialData()
        },
        onError: (err) => {
          console.error("SSE Stream error:", err)
          setMessages(prev => prev.map((msg, idx) => 
            idx === prev.length - 1 
              ? { ...msg, answer: err.message || "An error occurred while streaming synthesis. Please try again.", isStreaming: false } 
              : msg
          ))
          setIsLoading(false)
        }
      })
    } catch (e) {
      setIsLoading(false)
    }
  }

  const handleUpload = async () => {
    const fileInput = document.createElement("input")
    fileInput.type = "file"
    fileInput.accept = ".pdf,.txt"
    fileInput.onchange = async (e: any) => {
      const file = e.target.files?.[0]
      if (!file) return
      setUploadError(null)
      try {
        await uploadDocument(file)
        fetchInitialData()
      } catch (err: any) {
        setUploadError(err.message || "Failed to parse document.")
      }
    }
    fileInput.click()
  }

  const handleDelete = async (id: string) => {
    if (!confirm(`Delete ${id} and clear associated embeddings?`)) return
    try {
      await deleteDocument(id)
      fetchInitialData()
    } catch (e) {
      console.error("Deletion failed", e)
    }
  }

  const handleExcerptHighlight = (idx: number) => {
    setHighlightedExcerptIdx(idx)
    const cardEl = document.getElementById(`source-card-${idx}`)
    if (cardEl) {
      cardEl.scrollIntoView({ behavior: "smooth", block: "center" })
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

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          documents={documents}
          activeDocId={activeDocId}
          onSelect={(id) => setActiveDocId(id === activeDocId ? null : id)}
          onUploadClick={handleUpload}
          onDeleteDoc={handleDelete}
          queryCount={queryCount}
          queryLimit={30}
          selectedTopics={selectedTopics}
          onToggleTopic={handleToggleTopic}
        />

        {/* Center Panel */}
        <main className="flex-1 flex flex-col min-w-0 bg-term-bg-deep relative overflow-hidden">
          {/* Spotlight highlight background */}
          <Spotlight className="-top-40 left-10 md:left-60" fill="rgba(59, 130, 246, 0.08)" />
          
          {uploadError && (
            <div className="bg-term-dovish-red/10 border border-term-dovish-red/20 p-3 flex items-center space-x-2 text-xs text-term-dovish-red animate-fade-in relative z-20">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          {/* Empty Workspace Dashboard */}
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col justify-center items-center p-6 relative overflow-y-auto">
              <DotPattern className="absolute inset-0 opacity-15" />
              
              <div className="relative z-10 text-center max-w-lg mb-8 select-none">
                <h1 className="font-display text-2xl font-bold tracking-tight text-term-text-primary">
                  Macroeconomic Analysis Terminal
                </h1>
                <p className="text-xs text-term-text-secondary mt-2 max-w-sm mx-auto leading-relaxed">
                  Query Federal Open Market Committee minutes and transcripts with deep context vector search and citation grounding.
                </p>
              </div>

              {/* Policy Stance Drift Timeline */}
              {timeline.length > 0 && (
                <div className="relative z-10 w-full max-w-2xl px-2">
                  <SentimentTimeline data={timeline} />
                </div>
              )}

            </div>
          ) : (
            /* Scrollable Conversation Stream */
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
              {messages.map((msg, idx) => (
                <ResponseCard
                  key={idx}
                  query={msg.query}
                  answer={msg.answer}
                  excerpts={msg.excerpts}
                  confidence={msg.confidence}
                  metadata={msg.metadata}
                  isStreaming={msg.isStreaming}
                  onExcerptClick={handleExcerptHighlight}
                />
              ))}
              <div ref={chatEndRef} />
            </div>
          )}

          {/* Locked query composer */}
          <QueryInputBar
            onQuerySubmit={handleQuery}
            isLoading={isLoading}
            disabled={documents.length === 0}
          />
        </main>

        <EvidencePanel chunks={evidence} highlightedIndex={highlightedExcerptIdx} />
      </div>
    </div>
  )
}
