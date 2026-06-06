"use client"
import React, { useState, useEffect } from "react"
import { listDocuments, deleteDocument, uploadDocument } from "@/lib/api"
import { Topbar } from "@/components/Topbar"
import { ArrowLeft, FileText, Trash2, UploadCloud, CheckCircle2, ShieldAlert } from "lucide-react"
import Link from "next/link"
import { ShimmerButton } from "@/components/ui/shimmer-button"

interface Document {
  id: string
  name: string
  chunks: number
  date: string
  hawkish_score?: number
  topics?: string[]
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [healthData, setHealthData] = useState<any>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDocs()
  }, [])

  const fetchDocs = async () => {
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
      
      const hRes = await fetch("/api/health")
      if (hRes.ok) {
        setHealthData(await hRes.json())
      }
    } catch (e) {
      console.error("Failed to load documents", e)
    }
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setIsUploading(true)
    setError(null)
    try {
      await uploadDocument(file)
      fetchDocs()
    } catch (err: any) {
      setError(err.message || "Failed to upload document")
    } finally {
      setIsUploading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm(`Delete ${id} and wipe vectors?`)) return
    try {
      await deleteDocument(id)
      fetchDocs()
    } catch (e) {
      console.error("Failed to delete", e)
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
        {/* Navigation / Header */}
        <div className="flex items-center justify-between pb-4 border-b border-term-border select-none">
          <div className="flex items-center space-x-3">
            <Link
              href="/workspace"
              className="p-2 rounded bg-term-bg-panel hover:bg-term-bg-card border border-term-border text-term-text-secondary hover:text-term-text-primary transition-all cursor-pointer"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <h1 className="font-display text-xl font-bold tracking-tight text-term-text-primary">
                Document Index Manager
              </h1>
              <p className="text-xs text-term-text-secondary">
                Inspect, ingest, and delete FOMC meeting documents from the vector database.
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <label className="cursor-pointer">
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={handleUpload}
                className="hidden"
                disabled={isUploading}
              />
              <ShimmerButton
                shimmerColor="#3B82F6"
                background="rgba(21, 21, 31, 1)"
                borderRadius="6px"
                className="h-9 px-4 text-xs font-semibold text-term-accent-blue border border-term-accent-blue/30 cursor-pointer disabled:opacity-50"
              >
                <div className="flex items-center space-x-2">
                  <UploadCloud className="h-4 w-4" />
                  <span>{isUploading ? "Ingesting..." : "Ingest PDF/TXT"}</span>
                </div>
              </ShimmerButton>
            </label>
          </div>
        </div>

        {error && (
          <div className="bg-term-dovish-red/10 border border-term-dovish-red/20 p-4 rounded flex items-center space-x-2 text-xs text-term-dovish-red animate-fade-in">
            <ShieldAlert className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Documents Table */}
        <div className="bg-term-bg-panel border border-term-border rounded-lg overflow-hidden shadow-term-shadow">
          {documents.length === 0 ? (
            <div className="text-center py-20 px-4">
              <FileText className="h-10 w-10 text-term-text-muted mx-auto mb-3 opacity-55 animate-pulse" />
              <h3 className="text-sm font-semibold text-term-text-primary">No indexed files</h3>
              <p className="text-xs text-term-text-muted mt-1 max-w-xs mx-auto">
                Your semantic index is currently empty. Ingest transcripts or meeting minutes to begin using RAG queries.
              </p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse select-none">
              <thead>
                <tr className="border-b border-term-border bg-term-bg-deep/40 text-[10px] font-mono text-term-text-muted uppercase tracking-wider">
                  <th className="py-3 px-5 font-semibold">Document Name</th>
                  <th className="py-3 px-5 font-semibold">Meeting Date</th>
                  <th className="py-3 px-5 font-semibold">Sentiment</th>
                  <th className="py-3 px-5 font-semibold">Topics</th>
                  <th className="py-3 px-5 font-semibold">Chunks</th>
                  <th className="py-3 px-5 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-term-border text-xs">
                {documents.map((doc) => {
                  const score = doc.hawkish_score ?? 0.0
                  return (
                    <tr key={doc.id} className="hover:bg-term-bg-hover/10 transition-colors">
                      <td className="py-4 px-5 font-semibold flex items-center space-x-2.5 min-w-0">
                        <div className="p-1.5 rounded bg-term-accent-blue/10 text-term-accent-blue shrink-0">
                          <FileText className="h-4 w-4" />
                        </div>
                        <span className="truncate max-w-sm font-medium" title={doc.name}>
                          {doc.name.replace(/_/g, " ").replace(".pdf", "").replace(".txt", "")}
                        </span>
                      </td>
                      <td className="py-4 px-5 text-term-text-secondary font-mono">
                        {doc.date}
                      </td>
                      <td className="py-4 px-5 font-mono">
                        {score > 0.05 ? (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[9px] font-mono font-bold bg-term-hawkish-green/5 border border-term-hawkish-green/20 text-term-hawkish-green">
                            HAWKISH ({score > 0 ? "+" : ""}{score.toFixed(2)})
                          </span>
                        ) : score < -0.05 ? (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[9px] font-mono font-bold bg-term-dovish-red/5 border border-term-dovish-red/20 text-term-dovish-red">
                            DOVISH ({score.toFixed(2)})
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[9px] font-mono font-bold bg-term-accent-blue/5 border border-term-accent-blue/20 text-term-accent-blue">
                            NEUTRAL ({score.toFixed(2)})
                          </span>
                        )}
                      </td>
                      <td className="py-4 px-5">
                        <div className="flex flex-wrap gap-1 max-w-[250px]">
                          {doc.topics && doc.topics.length > 0 ? (
                            doc.topics.map((t, tid) => (
                              <span key={tid} className="px-1.5 py-0.5 rounded bg-term-bg-hover text-term-text-secondary text-[8px] font-mono border border-term-border uppercase tracking-tight">
                                {t}
                              </span>
                            ))
                          ) : (
                            <span className="text-[10px] text-term-text-muted italic">Unknown</span>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-5 text-term-text-secondary font-mono font-bold">
                        {doc.chunks}
                      </td>
                      <td className="py-4 px-5 text-right">
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="p-1.5 rounded hover:bg-term-dovish-red/15 hover:text-term-dovish-red text-term-text-muted transition-all cursor-pointer inline-flex items-center"
                          title="Delete document and erase vectors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
