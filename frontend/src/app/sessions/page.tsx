"use client"
import React, { useState, useEffect } from "react"
import { Topbar } from "@/components/Topbar"
import { ResponseCard, Excerpt } from "@/components/ResponseCard"
import { listSessions, getSessionHistory, deleteSession, listDocuments } from "@/lib/api"
import { ArrowLeft, History, Trash2, Search, Calendar, FileText, ChevronRight, HelpCircle } from "lucide-react"
import Link from "next/link"

interface Session {
  id: string
  name: string
  created_at: string
  updated_at: string
}

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
}

export default function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [healthData, setHealthData] = useState<any>(null)
  const [docCount, setDocCount] = useState(0)
  
  const [searchQuery, setSearchQuery] = useState("")
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [isLoadingSessions, setIsLoadingSessions] = useState(true)

  useEffect(() => {
    fetchInitialData()
  }, [])

  const fetchInitialData = async () => {
    setIsLoadingSessions(true)
    try {
      // 1. Fetch document count
      const docs = await listDocuments()
      setDocCount(docs.length)
      
      // 2. Fetch sessions
      const sessList = await listSessions()
      setSessions(sessList)
      if (sessList.length > 0) {
        // Auto-select first session
        handleSelectSession(sessList[0].id)
      }
      
      // 3. Fetch health
      const hRes = await fetch("/api/health")
      if (hRes.ok) {
        setHealthData(await hRes.json())
      }
    } catch (e) {
      console.error("Failed to load sessions data", e)
    } finally {
      setIsLoadingSessions(false)
    }
  }

  const handleSelectSession = async (id: string) => {
    setActiveSessionId(id)
    setIsLoadingHistory(true)
    try {
      const dbMessages = await getSessionHistory(id)
      
      // Group consecutive User/Assistant messages into unified pairs for ResponseCard
      const pairs: ChatMessage[] = []
      for (let i = 0; i < dbMessages.length; i++) {
        const msg = dbMessages[i]
        if (msg.role === "user") {
          const nextMsg = dbMessages[i + 1]
          if (nextMsg && nextMsg.role === "assistant") {
            const meta = (nextMsg.metadata || {}) as any
            const sources = meta.sources || []
            const similarityScores = meta.similarity_scores || []
            
            const mappedExcerpts: Excerpt[] = sources.map((s: any, idx: number) => ({
              num: idx + 1,
              page: s.page_number || 1,
              text: s.chunk_text || s.text || "",
              similarity: similarityScores[idx] || 0.80,
              source: s.source_document || "Unknown"
            }))

            const hasConfidence = meta.confidence !== undefined && meta.confidence !== null;
            const confidenceVal = hasConfidence && meta.confidence >= 0.7 
              ? "HIGH" 
              : hasConfidence && meta.confidence >= 0.5 
                ? "MEDIUM" 
                : "LOW";

            pairs.push({
              query: msg.content,
              answer: nextMsg.content,
              excerpts: mappedExcerpts,
              confidence: confidenceVal,
              metadata: {
                responseMs: meta.response_ms || 120,
                cacheHit: meta.cache_hit || false,
                chunksSearched: sources.length || 0,
                meetingDate: sources[0]?.meeting_date || "Unknown"
              }
            })
            i++ // Skip assistant message in next loop
          } else {
            pairs.push({
              query: msg.content,
              answer: "No response was recorded for this query.",
              excerpts: [],
              confidence: "LOW",
              metadata: {
                responseMs: 0,
                cacheHit: false,
                chunksSearched: 0,
                meetingDate: "Unknown"
              }
            })
          }
        } else {
          // Unpaired assistant message
           const meta = (msg.metadata || {}) as any
           const sources = meta.sources || []
           const similarityScores = meta.similarity_scores || []
           
           const mappedExcerpts: Excerpt[] = sources.map((s: any, idx: number) => ({
             num: idx + 1,
             page: s.page_number || 1,
             text: s.chunk_text || s.text || "",
             similarity: similarityScores[idx] || 0.80,
             source: s.source_document || "Unknown"
           }))

           const hasConfidence = meta.confidence !== undefined && meta.confidence !== null;
           const confidenceVal = hasConfidence && meta.confidence >= 0.7 
             ? "HIGH" 
             : hasConfidence && meta.confidence >= 0.5 
               ? "MEDIUM" 
               : "LOW";

           pairs.push({
             query: "Recorded response:",
             answer: msg.content,
             excerpts: mappedExcerpts,
             confidence: confidenceVal,
             metadata: {
               responseMs: meta.response_ms || 120,
               cacheHit: meta.cache_hit || false,
               chunksSearched: sources.length || 0,
               meetingDate: sources[0]?.meeting_date || "Unknown"
             }
           })
        }
      }
      setMessages(pairs)
    } catch (e) {
      console.error("Failed to load session history", e)
    } finally {
      setIsLoadingHistory(false)
    }
  }

  const handleDeleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!confirm("Are you sure you want to permanently delete this research session?")) return
    try {
      await deleteSession(id)
      const updatedList = sessions.filter(s => s.id !== id)
      setSessions(updatedList)
      
      if (activeSessionId === id) {
        if (updatedList.length > 0) {
          handleSelectSession(updatedList[0].id)
        } else {
          setActiveSessionId(null)
          setMessages([])
        }
      }
    } catch (e) {
      console.error("Failed to delete session", e)
    }
  }

  const formatDate = (isoStr: string) => {
    try {
      const date = new Date(isoStr)
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      })
    } catch (e) {
      return isoStr
    }
  }

  const filteredSessions = sessions.filter(s => 
    s.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="flex flex-col h-screen bg-term-bg-deep text-term-text-primary overflow-hidden w-full">
      <Topbar
        docCount={healthData?.indexed_documents || docCount}
        cacheCount={healthData?.cache_entries || 0}
        isBackendLive={!!healthData}
        model={healthData?.model || "gemini-2.5-flash"}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar: Session Directory */}
        <div className="w-80 border-r border-term-border bg-term-bg-panel flex flex-col overflow-hidden select-none">
          <div className="p-4 border-b border-term-border space-y-3">
            <div className="flex items-center space-x-3">
              <Link
                href="/workspace"
                className="p-1.5 rounded bg-term-bg-deep hover:bg-term-bg-card border border-term-border text-term-text-secondary hover:text-term-text-primary transition-all cursor-pointer"
              >
                <ArrowLeft className="h-4 w-4" />
              </Link>
              <div>
                <h2 className="font-display font-bold text-sm tracking-tight">Research History</h2>
                <p className="text-[10px] text-term-text-muted">Browse your past macroeconomic queries</p>
              </div>
            </div>

            {/* Search sessions */}
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-term-text-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search sessions..."
                className="w-full bg-term-bg-deep border border-term-border rounded py-1.5 pl-8 pr-3 text-xs text-term-text-primary focus:outline-none focus:border-term-accent-blue/50 placeholder-term-text-muted/60"
              />
            </div>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {isLoadingSessions ? (
              <div className="text-center py-10 text-xs text-term-text-muted font-mono animate-pulse">
                Loading query sessions...
              </div>
            ) : filteredSessions.length === 0 ? (
              <div className="text-center py-10 px-4">
                <History className="h-6 w-6 text-term-text-muted/40 mx-auto mb-2" />
                <p className="text-xs text-term-text-muted font-medium">No sessions found</p>
              </div>
            ) : (
              filteredSessions.map((session) => {
                const isActive = session.id === activeSessionId
                return (
                  <div
                    key={session.id}
                    onClick={() => handleSelectSession(session.id)}
                    className={`group w-full text-left p-3 rounded flex items-center justify-between border transition-all cursor-pointer select-none ${
                      isActive
                        ? "bg-term-accent-blue/10 border-term-accent-blue/30 text-term-accent-blue"
                        : "bg-transparent border-transparent hover:bg-term-bg-hover/10 text-term-text-secondary hover:text-term-text-primary"
                    }`}
                  >
                    <div className="min-w-0 flex-1 pr-2">
                      <div className="font-medium text-xs truncate max-w-[200px]" title={session.name}>
                        {session.name}
                      </div>
                      <div className="flex items-center space-x-1.5 text-[9px] text-term-text-muted mt-1 font-mono">
                        <Calendar className="h-3 w-3 shrink-0" />
                        <span>{formatDate(session.updated_at)}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => handleDeleteSession(e, session.id)}
                        className="p-1 rounded text-term-text-muted hover:text-term-dovish-red hover:bg-term-dovish-red/15 transition-all cursor-pointer"
                        title="Delete session"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                      <ChevronRight className="h-3.5 w-3.5 text-term-text-muted" />
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* Main Workspace Area: Session History Logs */}
        <div className="flex-1 bg-term-bg-deep flex flex-col overflow-y-auto">
          {activeSessionId ? (
            <div className="p-8 max-w-4xl mx-auto w-full space-y-8">
              <div className="pb-4 border-b border-term-border flex items-center justify-between select-none">
                <div>
                  <span className="text-[10px] font-mono text-term-accent-blue font-bold uppercase tracking-wider">
                    Query Log Session
                  </span>
                  <h1 className="font-display font-bold text-lg text-term-text-primary mt-0.5">
                    {sessions.find(s => s.id === activeSessionId)?.name || "Session History"}
                  </h1>
                </div>
                <div className="text-[9px] font-mono text-term-text-muted bg-term-bg-panel border border-term-border px-2.5 py-1 rounded">
                  SESSION ID: {activeSessionId}
                </div>
              </div>

              {isLoadingHistory ? (
                <div className="flex flex-col items-center justify-center py-32 space-y-3 font-mono text-xs text-term-text-muted animate-pulse">
                  <div className="w-6 h-6 rounded-full border border-t-term-accent-blue animate-spin"></div>
                  <span>Retrieving response history...</span>
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center py-32">
                  <HelpCircle className="h-8 w-8 text-term-text-muted/40 mx-auto mb-2" />
                  <p className="text-xs text-term-text-muted font-medium">No messages recorded in this session</p>
                </div>
              ) : (
                <div className="space-y-8">
                  {messages.map((msg, idx) => (
                    <ResponseCard
                      key={idx}
                      query={msg.query}
                      answer={msg.answer}
                      excerpts={msg.excerpts}
                      confidence={msg.confidence}
                      metadata={msg.metadata}
                      isStreaming={false}
                    />
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center select-none">
              <History className="h-12 w-12 text-term-text-muted mb-4 opacity-40 animate-pulse" />
              <h3 className="text-sm font-semibold text-term-text-primary">No Session Active</h3>
              <p className="text-xs text-term-text-muted mt-1.5 max-w-sm">
                Select a past grounded research session from the sidebar directory to inspect historical query parameters and synthesis logs.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
