"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  MessageSquare,
  Database,
  UploadCloud,
  Trash2,
  Loader2,
  FileText,
  Paperclip,
  ArrowUp,
  Plus,
  Menu,
  X,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  PanelRightClose,
  PanelRight,
  Check,
  CheckCircle,
  HelpCircle,
  Calendar,
  ShieldAlert,
} from "lucide-react";
import {
  queryDocumentsStream,
  uploadDocument,
  listDocuments,
  deleteDocument,
  listSessions,
  createSession,
  getSessionHistory,
  deleteSession,
  Document,
  QueryResponse,
  QuerySource,
} from "@/lib/api";

/* ─── Types ─── */
type UploadStep =
  | "uploading"
  | "extracting"
  | "chunking"
  | "embedding"
  | "indexing"
  | "success"
  | "idle";

interface ToastMessage {
  id: number;
  text: string;
  type: "success" | "error" | "info";
}

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  responseData?: QueryResponse;
  isTyping?: boolean;
}

interface ChatSession {
  id: string;
  title: string;
  history: ChatMessage[];
  sources: QuerySource[];
  scores: number[];
  confidence: number | null;
}

/* ─── Component ─── */
export default function Workspace() {
  /* ── State ── */
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [isLoading, setIsLoading] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);

  const [isUploading, setIsUploading] = useState(false);
  const [uploadStep, setUploadStep] = useState<UploadStep>("idle");
  const [uploadFilename, setUploadFilename] = useState("");
  const [uploadMessage, setUploadMessage] = useState<{
    text: string;
    type: "success" | "error" | "info";
  } | null>(null);

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(false);
  const [reasoningMode, setReasoningMode] = useState<
    "auto" | "research" | "resume" | "study" | "summary" | "compare"
  >("auto");
  const [highlightedChunkIndex, setHighlightedChunkIndex] = useState<
    number | null
  >(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);

  const evidencePanelRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  /* ── Helpers ── */
  const showToast = (
    text: string,
    type: "success" | "error" | "info" = "info"
  ) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, text, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  };

  /* ── Data Loading ── */
  useEffect(() => {
    fetchDocuments();
    fetchSessions();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [sessions, activeSessionId]);

  const fetchDocuments = async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error("Error loading documents:", err);
    }
  };

  const fetchSessions = async () => {
    try {
      const dbSessions = await listSessions();
      if (dbSessions && dbSessions.length > 0) {
        const mappedSessions: ChatSession[] = dbSessions.map((s) => ({
          id: s.id,
          title: s.name,
          history: [],
          sources: [],
          scores: [],
          confidence: null,
        }));
        setSessions(mappedSessions);
        const activeId = dbSessions[0].id;
        setActiveSessionId(activeId);
        loadSessionHistory(activeId, mappedSessions);
      } else {
        const defaultId = `session-${Date.now()}`;
        await createSession(defaultId, "New Conversation");
        setSessions([
          {
            id: defaultId,
            title: "New Conversation",
            history: [],
            sources: [],
            scores: [],
            confidence: null,
          },
        ]);
        setActiveSessionId(defaultId);
      }
    } catch (err) {
      console.error("Error loading sessions:", err);
    }
  };

  const loadSessionHistory = async (
    sessionId: string,
    currentSessionsList?: ChatSession[]
  ) => {
    try {
      const history = await getSessionHistory(sessionId);
      const localHistory: ChatMessage[] = history.map((h) => {
        const metadata = h.metadata || {};
        return {
          role: h.role,
          text: h.content,
          responseData:
            h.role === "assistant"
              ? {
                  answer: h.content,
                  citations: metadata.citations || [],
                  sources: metadata.sources || [],
                  similarity_scores: metadata.similarity_scores || [],
                  confidence:
                    metadata.confidence !== undefined
                      ? metadata.confidence
                      : 0,
                }
              : undefined,
        };
      });

      let lastSources: QuerySource[] = [];
      let lastScores: number[] = [];
      let lastConfidence: number | null = null;
      for (let i = localHistory.length - 1; i >= 0; i--) {
        const msg = localHistory[i];
        if (msg.role === "assistant" && msg.responseData) {
          lastSources = msg.responseData.sources || [];
          lastScores = msg.responseData.similarity_scores || [];
          lastConfidence =
            msg.responseData.confidence !== undefined
              ? msg.responseData.confidence
              : null;
          break;
        }
      }

      setSessions((prev) =>
        (currentSessionsList || prev).map((s) => {
          if (s.id === sessionId) {
            return {
              ...s,
              history: localHistory,
              sources: lastSources,
              scores: lastScores,
              confidence: lastConfidence,
            };
          }
          return s;
        })
      );

      setIsRightPanelOpen(lastSources.length > 0);
    } catch (err) {
      console.error(`Failed to load history for session ${sessionId}:`, err);
    }
  };

  const activeSession = sessions.find((s) => s.id === activeSessionId) ||
    sessions[0] || {
      id: "",
      title: "",
      history: [],
      sources: [],
      scores: [],
      confidence: null,
    };

  /* ── Query Handler ── */
  const handleQuery = async (
    e?: React.FormEvent,
    customQuery?: string
  ) => {
    if (e) e.preventDefault();
    const queryText = customQuery || query;
    if (!queryText.trim() || isLoading) return;

    setIsLoading(true);
    setHighlightedChunkIndex(null);
    setQuery("");
    setStatusMessage("Analyzing query intent...");
    const currentSessionId = activeSessionId;

    setSessions((prev) =>
      prev.map((s) => {
        if (s.id === currentSessionId) {
          const isDefaultTitle =
            s.title === "New Conversation" || s.title === "New Chat";
          return {
            ...s,
            title: isDefaultTitle
              ? queryText.length > 25
                ? queryText.slice(0, 22) + "..."
                : queryText
              : s.title,
            history: [...s.history, { role: "user", text: queryText }],
          };
        }
        return s;
      })
    );

    try {
      setSessions((prev) =>
        prev.map((s) => {
          if (s.id === currentSessionId) {
            return {
              ...s,
              history: [
                ...s.history,
                {
                  role: "assistant",
                  text: "",
                  isTyping: true,
                  responseData: {
                    answer: "",
                    citations: [],
                    sources: [],
                    similarity_scores: [],
                    confidence: 0,
                  },
                },
              ],
            };
          }
          return s;
        })
      );

      await queryDocumentsStream(
        queryText,
        topK,
        reasoningMode,
        currentSessionId,
        {
          onStatus: (status) => setStatusMessage(status),
          onMetadata: (metadata) => {
            setSessions((prev) =>
              prev.map((s) => {
                if (s.id === currentSessionId) {
                  const updatedHistory = [...s.history];
                  const lastMsg = updatedHistory[updatedHistory.length - 1];
                  if (lastMsg && lastMsg.role === "assistant") {
                    lastMsg.responseData = {
                      ...lastMsg.responseData,
                      sources: metadata.sources,
                      similarity_scores: metadata.similarity_scores,
                      confidence: metadata.confidence,
                    } as QueryResponse;
                  }
                  return {
                    ...s,
                    sources: metadata.sources || s.sources,
                    scores: metadata.similarity_scores || s.scores,
                    confidence:
                      metadata.confidence !== undefined
                        ? metadata.confidence
                        : s.confidence,
                    history: updatedHistory,
                  };
                }
                return s;
              })
            );
            if (metadata.sources && metadata.sources.length > 0) {
              setIsRightPanelOpen(true);
            }
          },
          onChunk: (chunk) => {
            setSessions((prev) =>
              prev.map((s) => {
                if (s.id === currentSessionId) {
                  const updatedHistory = [...s.history];
                  const lastMsg = updatedHistory[updatedHistory.length - 1];
                  if (lastMsg && lastMsg.role === "assistant") {
                    lastMsg.text += chunk;
                  }
                  return { ...s, history: updatedHistory };
                }
                return s;
              })
            );
          },
          onDone: () => {
            setStatusMessage("");
            setSessions((prev) =>
              prev.map((s) => {
                if (s.id === currentSessionId) {
                  const updatedHistory = [...s.history];
                  const lastMsg = updatedHistory[updatedHistory.length - 1];
                  if (lastMsg) lastMsg.isTyping = false;
                  return { ...s, history: updatedHistory };
                }
                return s;
              })
            );
            fetchSessions();
          },
          onError: (err) => {
            console.error(err);
            setStatusMessage("");
            setSessions((prev) =>
              prev.map((s) => {
                if (s.id === currentSessionId) {
                  return {
                    ...s,
                    history: [
                      ...s.history,
                      {
                        role: "assistant",
                        text: `Something went wrong. Please try again.`,
                      },
                    ],
                  };
                }
                return s;
              })
            );
          },
        }
      );
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
      setStatusMessage("");
    }
  };

  /* ── Session Handlers ── */
  const createNewSession = async () => {
    const newId = `session-${Date.now()}`;
    try {
      await createSession(newId, "New Conversation");
      const newSession: ChatSession = {
        id: newId,
        title: "New Conversation",
        history: [],
        sources: [],
        scores: [],
        confidence: null,
      };
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newId);
      setIsRightPanelOpen(false);
    } catch (err) {
      console.error("Failed to create session:", err);
      showToast("Failed to create conversation", "error");
    }
  };

  const selectSession = async (id: string) => {
    setActiveSessionId(id);
    await loadSessionHistory(id);
  };

  const handleDeleteSession = async (sessionId: string) => {
    if (sessions.length <= 1) {
      showToast("Cannot delete the only conversation", "error");
      return;
    }
    if (!confirm("Delete this conversation?")) return;
    try {
      await deleteSession(sessionId);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setSessions(remaining);
      if (activeSessionId === sessionId) {
        const nextActiveId = remaining[0].id;
        setActiveSessionId(nextActiveId);
        loadSessionHistory(nextActiveId, remaining);
      }
      showToast("Conversation deleted", "success");
    } catch (err) {
      console.error("Error deleting session:", err);
      showToast("Failed to delete conversation", "error");
    }
  };

  const selectSuggestedPrompt = (prompt: string) => {
    setQuery(prompt);
    handleQuery(undefined, prompt);
  };

  /* ── Citation Click ── */
  const handleCitationClick = (
    excerptNumber: number,
    messageSources?: QuerySource[],
    messageScores?: number[]
  ) => {
    const chunkIdx = excerptNumber - 1;
    
    // If sources exist for the clicked message, restore them dynamically in the sidebar
    if (messageSources && messageSources.length > 0) {
      setSessions((prev) =>
        prev.map((s) => {
          if (s.id === activeSessionId) {
            return {
              ...s,
              sources: messageSources,
              scores: messageScores || [],
            };
          }
          return s;
        })
      );
    }

    setHighlightedChunkIndex(chunkIdx);
    setIsRightPanelOpen(true);
    setTimeout(() => {
      const element = document.getElementById(`source-card-${chunkIdx}`);
      if (element)
        element.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 150);
  };

  /* ── Keyword Highlighting ── */
  const highlightKeywords = (text: string, keywordsStr: string) => {
    if (!keywordsStr || keywordsStr === "None") return text;
    const keywords = keywordsStr
      .split(",")
      .map((k) => k.trim())
      .filter((k) => k.length > 0);
    if (keywords.length === 0) return text;
    const escapedKeywords = keywords.map((k) =>
      k.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&")
    );
    const pattern = new RegExp(`\\b(${escapedKeywords.join("|")})\\b`, "gi");
    const parts = text.split(pattern);
    return parts.map((part, index) => {
      if (keywords.some((k) => k.toLowerCase() === part.toLowerCase())) {
        return (
          <span key={index} className="keyword-highlight">
            {part}
          </span>
        );
      }
      return part;
    });
  };

  /* ── Text Formatter ── */
  const formatText = (text: string, msgSources?: QuerySource[], msgScores?: number[]) => {
    if (!text) return null;
    const lines = text.split("\n");
    const elements: React.ReactNode[] = [];
    let i = 0;

    const renderInline = (line: string, keyPrefix: string) => {
      const parts = line.split(/(\[Excerpt \d+\])/g);
      return parts.map((part, pIdx) => {
        const match = part.match(/\[Excerpt (\d+)\]/);
        if (match) {
          const num = parseInt(match[1]);
          return (
            <button
              key={`${keyPrefix}-cite-${pIdx}`}
              onClick={() => handleCitationClick(num, msgSources, msgScores)}
              className="inline-flex items-center mx-1 px-1.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-[var(--accent-dim)] hover:bg-[var(--accent)]/20 border border-[var(--accent)]/20 text-[var(--accent)] cursor-pointer transition-colors duration-150"
            >
              [{num}]
            </button>
          );
        }
        const boldParts = part.split(/(\*{1,2}[^*]+\*{1,2})/g);
        return (
          <span key={`${keyPrefix}-${pIdx}`}>
            {boldParts.map((bp, bpIdx) => {
              if (
                (bp.startsWith("**") && bp.endsWith("**")) ||
                (bp.startsWith("*") && bp.endsWith("*"))
              ) {
                const cleanText = bp.replace(/\*/g, "");
                return (
                  <strong
                    key={bpIdx}
                    className="font-semibold text-[var(--text-primary)]"
                  >
                    {cleanText}
                  </strong>
                );
              }
              return bp;
            })}
          </span>
        );
      });
    };

    while (i < lines.length) {
      const line = lines[i];
      if (line.trim() === "") {
        i++;
        continue;
      }
      const headingMatch = line.match(/^(#{1,3})\s+(.+)/);
      if (headingMatch) {
        const level = headingMatch[1].length;
        const headText = headingMatch[2];
        const cls =
          level === 1
            ? "text-[15px] font-semibold text-[var(--text-primary)] mt-5 mb-2.5 tracking-tight"
            : level === 2
            ? "text-[14px] font-semibold text-[var(--text-primary)] mt-4 mb-2"
            : "text-[13px] font-medium text-[var(--text-secondary)] mt-3 mb-1.5";
        elements.push(
          <div key={`h-${i}`} className={cls}>
            {renderInline(headText, `h-${i}`)}
          </div>
        );
        i++;
        continue;
      }
      if (/^\s*[-*]\s+/.test(line)) {
        const listItems: string[] = [];
        while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
          listItems.push(lines[i].replace(/^\s*[-*]\s+/, ""));
          i++;
        }
        elements.push(
          <ul
            key={`ul-${i}`}
            className="list-disc list-inside space-y-1.5 mb-3.5 ml-1 marker:text-[var(--text-quaternary)]"
          >
            {listItems.map((item, liIdx) => (
              <li
                key={liIdx}
                className="text-[13px] text-[var(--text-secondary)] leading-relaxed"
              >
                {renderInline(item, `ul-${i}-${liIdx}`)}
              </li>
            ))}
          </ul>
        );
        continue;
      }
      if (/^\s*\d+\.\s+/.test(line)) {
        const listItems: string[] = [];
        while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
          listItems.push(lines[i].replace(/^\s*\d+\.\s+/, ""));
          i++;
        }
        elements.push(
          <ol
            key={`ol-${i}`}
            className="list-decimal list-inside space-y-1.5 mb-3.5 ml-1 marker:text-[var(--text-quaternary)]"
          >
            {listItems.map((item, liIdx) => (
              <li
                key={liIdx}
                className="text-[13px] text-[var(--text-secondary)] leading-relaxed"
              >
                {renderInline(item, `ol-${i}-${liIdx}`)}
              </li>
            ))}
          </ol>
        );
        continue;
      }
      elements.push(
        <p
          key={`p-${i}`}
          className="mb-3.5 text-[13px] text-[var(--text-secondary)] leading-[1.7] last:mb-0"
        >
          {renderInline(line, `p-${i}`)}
        </p>
      );
      i++;
    }
    return elements;
  };

  /* ── Upload Pipeline ── */
  const triggerFileInput = () => fileInputRef.current?.click();

  const handleFileChange = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (e.target.files && e.target.files[0]) {
      processUploadedFile(e.target.files[0]);
    }
  };

  const processUploadedFile = async (file: File) => {
    setIsUploading(true);
    setUploadFilename(file.name);
    setUploadMessage(null);
    setUploadStep("uploading");
    setTimeout(() => setUploadStep("extracting"), 1000);
    setTimeout(() => setUploadStep("chunking"), 2500);
    setTimeout(() => setUploadStep("embedding"), 4000);
    setTimeout(() => setUploadStep("indexing"), 5500);
    try {
      const res = await uploadDocument(file);
      setUploadStep("success");
      setUploadMessage({
        text: `${file.name} indexed — ${res.chunks || 0} chunks created.`,
        type: "success",
      });
      fetchDocuments();
    } catch (err: any) {
      console.error(err);
      setUploadStep("idle");
      setUploadMessage({
        text: err.message || "Failed to process document.",
        type: "error",
      });
    } finally {
      setTimeout(() => {
        setIsUploading(false);
        setUploadMessage(null);
        setUploadStep("idle");
      }, 4000);
    }
  };

  const handleDeleteDoc = async (docId: string) => {
    if (!confirm(`Remove '${docId}' from index?`)) return;
    try {
      await deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      fetchDocuments();
      showToast(`Removed ${docId}`, "info");
    } catch (err) {
      console.error(err);
      showToast("Failed to remove document", "error");
    }
  };

  /* ── Drag & Drop ── */
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.name.endsWith(".pdf") || file.name.endsWith(".txt")) {
        processUploadedFile(file);
      } else {
        showToast("Only PDF and TXT files are supported", "error");
      }
    }
  };

  /* ─── RENDER ─── */
  const suggestions = [
    "What did the FOMC say about inflation?",
    "Summarize the latest meeting minutes",
    "Compare monetary policy across meetings",
  ];

  return (
    <div
      className="flex h-screen w-screen bg-[var(--bg-root)] text-[var(--text-primary)] font-sans antialiased overflow-hidden relative"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* ─── Toast System ─── */}
      <div className="fixed top-5 right-5 z-[100] flex flex-col space-y-2 pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto px-4 py-2.5 rounded-xl text-xs font-medium shadow-lg backdrop-blur-xl flex items-center space-x-2 animate-slide-in ${
              toast.type === "success"
                ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                : toast.type === "error"
                ? "bg-rose-500/10 border border-rose-500/20 text-rose-400"
                : "glass text-[var(--text-secondary)]"
            }`}
          >
            {toast.type === "success" && <Check className="h-3.5 w-3.5" />}
            <span>{toast.text}</span>
          </div>
        ))}
      </div>

      {/* ─── Drag Overlay ─── */}
      {isDragOver && (
        <div className="absolute inset-0 z-[90] bg-[var(--bg-root)]/90 backdrop-blur-lg flex items-center justify-center animate-fade-in">
          <div className="p-12 rounded-2xl border-2 border-dashed border-[var(--accent)]/40 bg-[var(--accent-glow)] text-center">
            <UploadCloud className="h-10 w-10 text-[var(--accent)] mx-auto mb-4" />
            <p className="text-sm font-medium text-[var(--text-primary)]">
              Drop to analyze
            </p>
            <p className="text-xs text-[var(--text-tertiary)] mt-1">
              PDF or TXT
            </p>
          </div>
        </div>
      )}

      {/* ─── LEFT SIDEBAR ─── */}
      <aside
        className={`shrink-0 h-full flex flex-col justify-between transition-all duration-300 ease-in-out ${
          isSidebarOpen
            ? "w-64 border-r border-[var(--border-subtle)]"
            : "w-0 overflow-hidden"
        }`}
        style={{
          background:
            "linear-gradient(180deg, rgba(17,17,20,0.95) 0%, rgba(10,10,12,0.98) 100%)",
          backdropFilter: "blur(20px)",
        }}
      >
        <div className="flex-1 flex flex-col min-h-0">
          {/* Logo */}
          <div className="px-5 pt-5 pb-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div
                className="h-7 w-7 rounded-lg flex items-center justify-center"
                style={{
                  background:
                    "linear-gradient(135deg, var(--accent) 0%, #C4956A 100%)",
                  boxShadow: "0 2px 12px rgba(212, 165, 116, 0.2)",
                }}
              >
                <span className="text-[11px] font-bold text-[var(--bg-root)]">
                  CK
                </span>
              </div>
              <span className="font-serif text-sm font-medium tracking-wide text-[var(--text-primary)]">
                Workspace
              </span>
            </div>
            <button
              onClick={() => setIsSidebarOpen(false)}
              className="p-1.5 rounded-lg text-[var(--text-quaternary)] hover:text-[var(--text-secondary)] hover:bg-white/[0.03] cursor-pointer transition-colors"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* New Conversation */}
          <div className="px-4 pb-4">
            <button
              onClick={createNewSession}
              className="w-full py-2.5 px-3 rounded-xl text-xs font-medium flex items-center justify-center space-x-2 cursor-pointer transition-all duration-200 border border-[var(--border-default)] hover:border-[var(--border-hover)] bg-white/[0.02] hover:bg-white/[0.04] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>New conversation</span>
            </button>
          </div>

          {/* Sessions */}
          <div className="flex-1 overflow-y-auto px-3">
            <div className="px-2 mb-3">
              <span className="text-[10px] font-medium text-[var(--text-quaternary)] uppercase tracking-[0.08em]">
                Conversations
              </span>
            </div>
            <div className="space-y-0.5">
              {sessions.map((s) => {
                const isActive = s.id === activeSessionId;
                return (
                  <div
                    key={s.id}
                    className={`group w-full flex items-center justify-between rounded-xl transition-all duration-150 ${
                      isActive
                        ? "bg-white/[0.05] text-[var(--text-primary)]"
                        : "text-[var(--text-tertiary)] hover:bg-white/[0.02] hover:text-[var(--text-secondary)]"
                    }`}
                  >
                    <button
                      onClick={() => selectSession(s.id)}
                      className="flex-1 text-left py-2.5 px-3 text-[12px] flex items-center space-x-2.5 cursor-pointer truncate"
                    >
                      <MessageSquare
                        className={`h-3.5 w-3.5 shrink-0 ${
                          isActive
                            ? "text-[var(--accent)]"
                            : "text-[var(--text-quaternary)]"
                        }`}
                      />
                      <span className="truncate">{s.title}</span>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteSession(s.id);
                      }}
                      className="p-1.5 opacity-0 group-hover:opacity-100 hover:bg-rose-500/10 rounded-lg mr-1.5 text-[var(--text-quaternary)] hover:text-rose-400 transition-all cursor-pointer shrink-0"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Bottom */}
        <div className="p-4 border-t border-[var(--border-subtle)]">
          <div className="flex items-center space-x-2.5">
            <div className="h-7 w-7 rounded-full bg-white/[0.06] text-[var(--text-secondary)] font-medium flex items-center justify-center text-[10px] select-none">
              CK
            </div>
            <span className="text-[11px] text-[var(--text-tertiary)]">
              {documents.length} documents indexed
            </span>
          </div>
        </div>
      </aside>

      {/* ─── MAIN AREA ─── */}
      <main className="flex-1 flex flex-col min-w-0 h-full relative">
        {/* Sidebar Toggle */}
        {!isSidebarOpen && (
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="absolute top-4 left-4 z-50 p-2 rounded-xl glass hover:bg-white/[0.04] text-[var(--text-quaternary)] hover:text-[var(--text-secondary)] cursor-pointer transition-all"
          >
            <Menu className="h-4 w-4" />
          </button>
        )}

        {/* Header */}
        <header className="h-12 flex items-center justify-between px-6 border-b border-[var(--border-subtle)] bg-[var(--bg-root)]/80 backdrop-blur-md sticky top-0 z-40">
          <div className="flex items-center ml-10 md:ml-0">
            <span className="text-[12px] font-medium text-[var(--text-tertiary)]">
              {activeSession.title !== "New Conversation"
                ? activeSession.title
                : "Workspace"}
            </span>
          </div>
          <button
            onClick={() => setIsRightPanelOpen(!isRightPanelOpen)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium cursor-pointer transition-all duration-200 ${
              isRightPanelOpen
                ? "bg-[var(--accent-dim)] border border-[var(--accent)]/20 text-[var(--accent)]"
                : "border border-[var(--border-subtle)] hover:border-[var(--border-hover)] text-[var(--text-quaternary)] hover:text-[var(--text-secondary)]"
            }`}
          >
            {isRightPanelOpen ? (
              <PanelRightClose className="h-3.5 w-3.5" />
            ) : (
              <PanelRight className="h-3.5 w-3.5" />
            )}
            <span>Sources</span>
          </button>
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto min-h-0 flex flex-col">
          <div className="max-w-2xl w-full mx-auto flex-1 flex flex-col px-6 py-6">
            {activeSession.history.length === 0 ? (
              /* ─── EMPTY STATE ─── */
              <div className="flex-1 flex flex-col justify-center items-center text-center animate-fade-in">
                {/* Animated Orb */}
                <div className="relative mb-10">
                  <div
                    className="h-20 w-20 rounded-full animate-orb"
                    style={{
                      background:
                        "radial-gradient(circle at 35% 35%, rgba(212, 165, 116, 0.4) 0%, rgba(212, 165, 116, 0.08) 50%, transparent 70%)",
                    }}
                  />
                  <div
                    className="absolute inset-0 h-20 w-20 rounded-full animate-float"
                    style={{
                      background:
                        "radial-gradient(circle at 60% 60%, rgba(212, 165, 116, 0.15) 0%, transparent 60%)",
                    }}
                  />
                </div>

                <h1 className="text-2xl font-serif font-medium text-[var(--text-primary)] tracking-tight leading-tight animate-fade-in-up delay-100">
                  What would you like to analyze?
                </h1>
                <p className="text-[13px] text-[var(--text-quaternary)] mt-3 max-w-sm leading-relaxed animate-fade-in-up delay-200">
                  Upload documents and ask questions. Your workspace learns
                  from every interaction.
                </p>

                {/* Suggestion Pills */}
                <div className="flex flex-wrap justify-center gap-2 mt-8 max-w-lg animate-fade-in-up delay-300">
                  {suggestions.map((s, idx) => (
                    <button
                      key={idx}
                      onClick={() => selectSuggestedPrompt(s)}
                      className="px-4 py-2 rounded-full text-[12px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)] hover:border-[var(--border-hover)] bg-white/[0.01] hover:bg-white/[0.03] cursor-pointer transition-all duration-200"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              /* ─── MESSAGE THREAD ─── */
              <div className="space-y-10 flex-1 py-4 animate-fade-in">
                {activeSession.history.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {msg.role === "user" ? (
                      /* User Message */
                      <div className="max-w-[80%] animate-fade-in-up">
                        <div className="bg-white/[0.04] border border-[var(--border-subtle)] rounded-2xl px-5 py-3.5">
                          <p className="text-[14px] text-[var(--text-primary)] whitespace-pre-wrap leading-relaxed">
                            {msg.text}
                          </p>
                        </div>
                      </div>
                    ) : (
                      /* Assistant Message */
                      <div className="flex items-start space-x-4 max-w-[95%] w-full animate-fade-in-up">
                        <div
                          className="h-7 w-7 rounded-full flex items-center justify-center shrink-0 mt-0.5"
                          style={{
                            background:
                              "linear-gradient(135deg, rgba(212,165,116,0.25) 0%, rgba(212,165,116,0.08) 100%)",
                          }}
                        >
                          <div className="h-2.5 w-2.5 rounded-full bg-[var(--accent)]" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="markdown-body">
                            {formatText(msg.text, msg.responseData?.sources, msg.responseData?.similarity_scores)}
                          </div>

                          {/* Controls */}
                          {!msg.isTyping && msg.text && (
                            <div className="mt-5 flex items-center justify-between pt-3 border-t border-[var(--border-subtle)]">
                              {/* Confidence */}
                              {msg.responseData &&
                                msg.responseData.confidence > 0 && (
                                  <div className="flex items-center space-x-2 text-[10px] text-[var(--text-quaternary)]">
                                    <div
                                      className={`h-1.5 w-1.5 rounded-full ${
                                        msg.responseData.confidence >= 0.55
                                          ? "bg-emerald-400"
                                          : "bg-amber-400"
                                      }`}
                                    />
                                    <span>
                                      {msg.responseData.confidence >= 0.55
                                        ? "High"
                                        : "Medium"}{" "}
                                      confidence
                                    </span>
                                  </div>
                                )}
                              {msg.responseData &&
                                msg.responseData.confidence === 0 && (
                                  <div className="flex items-center space-x-1.5 text-[10px] text-[var(--text-quaternary)]">
                                    <ShieldAlert className="h-3 w-3" />
                                    <span>Unverified</span>
                                  </div>
                                )}
                              {!msg.responseData && <div />}

                              <div className="flex items-center space-x-1">
                                <button
                                  onClick={() => {
                                    navigator.clipboard.writeText(msg.text);
                                    showToast("Copied", "success");
                                  }}
                                  className="p-1.5 rounded-lg text-[var(--text-quaternary)] hover:text-[var(--text-secondary)] hover:bg-white/[0.03] transition-colors cursor-pointer"
                                  title="Copy"
                                >
                                  <Copy className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  className="p-1.5 rounded-lg text-[var(--text-quaternary)] hover:text-[var(--text-secondary)] hover:bg-white/[0.03] transition-colors cursor-pointer"
                                  title="Helpful"
                                >
                                  <ThumbsUp className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  className="p-1.5 rounded-lg text-[var(--text-quaternary)] hover:text-[var(--text-secondary)] hover:bg-white/[0.03] transition-colors cursor-pointer"
                                  title="Not helpful"
                                >
                                  <ThumbsDown className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  onClick={() =>
                                    selectSuggestedPrompt(
                                      activeSession.history[idx - 1]?.text ||
                                        ""
                                    )
                                  }
                                  className="p-1.5 rounded-lg text-[var(--text-quaternary)] hover:text-[var(--text-secondary)] hover:bg-white/[0.03] transition-colors cursor-pointer"
                                  title="Regenerate"
                                >
                                  <RotateCcw className="h-3.5 w-3.5" />
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {/* Upload Progress */}
                {isUploading && (
                  <div className="flex justify-start animate-fade-in-up">
                    <div
                      className="h-7 w-7 rounded-full flex items-center justify-center shrink-0 mr-4 mt-0.5"
                      style={{
                        background:
                          "linear-gradient(135deg, rgba(212,165,116,0.25) 0%, rgba(212,165,116,0.08) 100%)",
                      }}
                    >
                      <div className="h-2.5 w-2.5 rounded-full bg-[var(--accent)]" />
                    </div>
                    <div className="glass-elevated rounded-2xl p-5 max-w-sm text-xs space-y-3 flex-1">
                      <div className="text-[10px] font-medium text-[var(--text-quaternary)] uppercase tracking-[0.06em] flex items-center">
                        <Loader2 className="h-3 w-3 animate-spin text-[var(--accent)] mr-2" />
                        Indexing {uploadFilename}
                      </div>

                      <div className="space-y-2 text-[11px]">
                        {[
                          {
                            step: "uploading",
                            label: "Uploading",
                          },
                          {
                            step: "extracting",
                            label: "Extracting text",
                          },
                          {
                            step: "chunking",
                            label: "Chunking sections",
                          },
                          {
                            step: "embedding",
                            label: "Generating embeddings",
                          },
                          {
                            step: "indexing",
                            label: "Storing vectors",
                          },
                        ].map(({ step, label }, stepIdx) => {
                          const steps = [
                            "uploading",
                            "extracting",
                            "chunking",
                            "embedding",
                            "indexing",
                            "success",
                          ];
                          const currentIdx = steps.indexOf(uploadStep);
                          const thisIdx = steps.indexOf(step);
                          const isDone = currentIdx > thisIdx;
                          const isActive = currentIdx === thisIdx;
                          return (
                            <div
                              key={stepIdx}
                              className="flex items-center space-x-2.5"
                            >
                              {isDone ? (
                                <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                              ) : isActive ? (
                                <Loader2 className="h-3.5 w-3.5 animate-spin text-[var(--accent)]" />
                              ) : (
                                <HelpCircle className="h-3.5 w-3.5 text-[var(--text-quaternary)]" />
                              )}
                              <span
                                className={
                                  isActive
                                    ? "text-[var(--text-primary)] font-medium"
                                    : isDone
                                    ? "text-[var(--text-tertiary)]"
                                    : "text-[var(--text-quaternary)]"
                                }
                              >
                                {label}
                              </span>
                            </div>
                          );
                        })}
                      </div>

                      {uploadMessage && (
                        <div className="mt-2 text-[10px] text-emerald-400 bg-emerald-500/5 border border-emerald-500/15 px-3 py-1.5 rounded-lg">
                          {uploadMessage.text}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Loading */}
                {isLoading && (
                  <div className="flex justify-start animate-fade-in">
                    <div
                      className="h-7 w-7 rounded-full flex items-center justify-center shrink-0 mr-4 mt-0.5"
                      style={{
                        background:
                          "linear-gradient(135deg, rgba(212,165,116,0.25) 0%, rgba(212,165,116,0.08) 100%)",
                      }}
                    >
                      <div className="h-2.5 w-2.5 rounded-full bg-[var(--accent)]" />
                    </div>
                    <div className="glass rounded-2xl px-5 py-4 flex items-center space-x-3 max-w-sm">
                      <Loader2 className="h-4 w-4 animate-spin text-[var(--accent)]" />
                      <span className="text-[12px] text-[var(--text-tertiary)]">
                        {statusMessage || "Thinking..."}
                      </span>
                    </div>
                  </div>
                )}

                <div ref={chatEndRef} />
              </div>
            )}

            {/* ─── FLOATING COMPOSER ─── */}
            <form
              onSubmit={handleQuery}
              className="mt-auto pt-4 sticky bottom-0 z-30"
            >
              <div
                className="relative rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-default)] shadow-lg composer-glow transition-all max-w-2xl mx-auto overflow-hidden"
              >
                {/* Input */}
                <div className="flex items-center px-5 py-4">
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask anything..."
                    className="flex-1 bg-transparent text-[14px] text-[var(--text-primary)] placeholder-[var(--text-quaternary)] focus:outline-none"
                    disabled={isLoading || isUploading}
                  />
                </div>

                {/* Toolbar */}
                <div className="flex items-center justify-between px-4 py-2.5 border-t border-[var(--border-subtle)]">
                  <div className="flex items-center space-x-1">
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileChange}
                      className="hidden"
                      accept=".pdf,.txt"
                    />
                    <button
                      type="button"
                      onClick={triggerFileInput}
                      disabled={isLoading || isUploading}
                      className="p-2 rounded-lg text-[var(--text-quaternary)] hover:text-[var(--text-secondary)] hover:bg-white/[0.03] cursor-pointer disabled:opacity-30 transition-colors"
                      title="Attach document"
                    >
                      <Paperclip className="h-4 w-4" />
                    </button>

                    <div className="flex items-center text-[var(--text-quaternary)] border border-[var(--border-subtle)] px-2.5 py-1 rounded-lg text-[10px] ml-1">
                      <select
                        value={reasoningMode}
                        onChange={(e) =>
                          setReasoningMode(e.target.value as typeof reasoningMode)
                        }
                        className="bg-transparent text-[var(--text-tertiary)] font-medium focus:outline-none cursor-pointer border-none text-[10px]"
                      >
                        <option value="auto" className="bg-[var(--bg-surface)]">
                          Auto
                        </option>
                        <option
                          value="research"
                          className="bg-[var(--bg-surface)]"
                        >
                          Research
                        </option>
                        <option
                          value="resume"
                          className="bg-[var(--bg-surface)]"
                        >
                          Resume
                        </option>
                        <option
                          value="study"
                          className="bg-[var(--bg-surface)]"
                        >
                          Study
                        </option>
                        <option
                          value="summary"
                          className="bg-[var(--bg-surface)]"
                        >
                          Summary
                        </option>
                        <option
                          value="compare"
                          className="bg-[var(--bg-surface)]"
                        >
                          Compare
                        </option>
                      </select>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={!query.trim() || isLoading || isUploading}
                    className="h-8 w-8 rounded-full flex items-center justify-center transition-all duration-200 cursor-pointer disabled:opacity-20"
                    style={{
                      background:
                        query.trim() && !isLoading
                          ? "linear-gradient(135deg, var(--accent) 0%, #C4956A 100%)"
                          : "rgba(255,255,255,0.04)",
                      color:
                        query.trim() && !isLoading
                          ? "var(--bg-root)"
                          : "var(--text-quaternary)",
                    }}
                  >
                    <ArrowUp className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="h-4" />
            </form>
          </div>
        </div>
      </main>

      {/* ─── RIGHT EVIDENCE PANEL ─── */}
      <aside
        className={`shrink-0 h-full flex flex-col transition-all duration-300 ease-in-out border-l ${
          isRightPanelOpen
            ? "w-[380px] lg:w-[400px] border-[var(--border-subtle)]"
            : "w-0 overflow-hidden border-transparent"
        }`}
        style={{
          background:
            "linear-gradient(180deg, rgba(14,14,17,0.98) 0%, rgba(10,10,12,1) 100%)",
        }}
      >
        {/* Panel Header */}
        <div className="px-5 py-4 flex items-center justify-between border-b border-[var(--border-subtle)]">
          <div className="flex items-center space-x-2.5">
            <Database className="h-3.5 w-3.5 text-[var(--accent)]" />
            <span className="text-[12px] font-medium text-[var(--text-secondary)]">
              Sources
            </span>
          </div>
          <button
            onClick={() => setIsRightPanelOpen(false)}
            className="p-1.5 rounded-lg text-[var(--text-quaternary)] hover:text-[var(--text-secondary)] hover:bg-white/[0.03] cursor-pointer transition-colors"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Sources List */}
        <div
          ref={evidencePanelRef}
          className="flex-1 overflow-y-auto p-4 space-y-3"
        >
          {activeSession.sources.length === 0 ? (
            <div className="h-full flex flex-col justify-center items-center text-center p-8">
              <div
                className="h-10 w-10 rounded-full flex items-center justify-center mb-4"
                style={{
                  background:
                    "radial-gradient(circle, rgba(212,165,116,0.08) 0%, transparent 70%)",
                }}
              >
                <FileText className="h-4 w-4 text-[var(--text-quaternary)]" />
              </div>
              <p className="text-[12px] text-[var(--text-quaternary)]">
                Sources will appear here
              </p>
            </div>
          ) : (
            activeSession.sources.map((source, idx) => {
              const similarityScore = activeSession.scores[idx] || 0;
              const scorePercent = Math.round(similarityScore * 100);
              const isHighlighted = highlightedChunkIndex === idx;
              const meta = source as unknown as Record<string, unknown>;
              const matchedKeywords =
                (meta.matched_keywords as string) || "None";
              const sectionName =
                (meta.section_name as string) || "Overview";

              return (
                <div
                  id={`source-card-${idx}`}
                  key={idx}
                  className={`rounded-xl p-4 border transition-all duration-200 ${
                    isHighlighted
                      ? "bg-[var(--accent-glow)] border-[var(--accent)]/30 shadow-lg"
                      : "bg-white/[0.015] border-[var(--border-subtle)] hover:border-[var(--border-hover)]"
                  }`}
                >
                  {/* Header */}
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-medium text-[var(--accent)] bg-[var(--accent-dim)] px-2 py-0.5 rounded-full">
                      Excerpt {idx + 1} · {scorePercent}%
                    </span>
                    <span className="text-[10px] text-[var(--text-quaternary)]">
                      {sectionName}
                    </span>
                  </div>

                  {/* Content */}
                  <div className="text-[11px] text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap bg-white/[0.01] p-3 rounded-lg border border-[var(--border-subtle)]">
                    {highlightKeywords(
                      source.chunk_text || (source as any).text || "",
                      matchedKeywords
                    )}
                  </div>

                  {/* Keywords */}
                  {matchedKeywords !== "None" && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {matchedKeywords.split(", ").map(
                        (kw: string, kwIdx: number) => (
                          <span
                            key={kwIdx}
                            className="px-1.5 py-0.5 bg-[var(--accent-dim)] text-[var(--accent)] text-[9px] rounded font-medium"
                          >
                            {kw}
                          </span>
                        )
                      )}
                    </div>
                  )}

                  {/* Footer */}
                  <div className="mt-3 pt-2.5 border-t border-[var(--border-subtle)] flex items-center justify-between text-[9px] text-[var(--text-quaternary)]">
                    <div className="flex items-center space-x-1.5 max-w-[55%]">
                      <FileText className="h-3 w-3 text-[var(--accent)] shrink-0 opacity-60" />
                      <span className="truncate">
                        {source.source_document}
                      </span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Calendar className="h-3 w-3 opacity-50" />
                      <span>{source.meeting_date}</span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </aside>
    </div>
  );
}
