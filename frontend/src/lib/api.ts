export interface Document {
  id: string;
  name: string;
  date: string;
  chunks: number;
}

export interface QuerySource {
  meeting_date: string;
  chunk_index: string;
  chunk_id: string;
  source_document: string;
  chunk_text?: string;
  page_number?: number;
}

export interface QueryResponse {
  answer: string;
  citations: string[];
  sources: QuerySource[];
  similarity_scores: number[];
  confidence: number;
}

export interface UploadResponse {
  message: string;
  status: string;
  chunks?: number;
  meeting_date?: string;
}

export interface Session {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: {
    citations?: string[];
    sources?: QuerySource[];
    similarity_scores?: number[];
    confidence?: number;
  };
}

const API_BASE_URL = '/api';

export async function queryDocuments(query: string, topK: number = 5, mode: string = "auto", sessionId?: string): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, top_k: topK, mode, session_id: sessionId }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to query documents');
  }

  return response.json();
}

export async function queryDocumentsStream(
  query: string,
  topK: number = 5,
  mode: string = "auto",
  sessionId?: string,
  callbacks: {
    onStatus?: (status: string) => void;
    onMetadata?: (metadata: any) => void;
    onChunk?: (chunk: string) => void;
    onDone?: (data: any) => void;
    onError?: (error: any) => void;
  } = {}
) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, 45000); // 45 seconds timeout

  try {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, top_k: topK, mode, session_id: sessionId }),
      signal: controller.signal,
    });

    // NOTE: Do NOT clearTimeout here — the timeout must cover the entire
    // SSE stream, not just the initial connection. Cleanup is in finally{}.

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No readable stream available");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || "";

      for (const block of lines) {
        if (!block.trim()) continue;
        
        const eventMatch = block.match(/^event:\s*(.+)$/m);
        const dataMatch = block.match(/^data:\s*(.+)$/m);
        
        if (eventMatch && dataMatch) {
          const event = eventMatch[1].trim();
          const rawData = dataMatch[1].trim();
          
          let parsedData = rawData;
          try {
            parsedData = JSON.parse(rawData);
          } catch (e) {
            // keep rawData if not json
          }

          if (event === "status" && callbacks.onStatus) {
            callbacks.onStatus(parsedData as string);
          } else if (event === "metadata" && callbacks.onMetadata) {
            callbacks.onMetadata(parsedData);
          } else if (event === "chunk" && callbacks.onChunk) {
            callbacks.onChunk(parsedData as string);
          } else if (event === "done" && callbacks.onDone) {
            callbacks.onDone(parsedData);
          }
        }
      }
    }
  } catch (error: any) {
    if (error.name === 'AbortError') {
      if (callbacks.onError) {
        callbacks.onError(new Error("Request timed out after 30 seconds. Please try again."));
      }
    } else {
      if (callbacks.onError) {
        callbacks.onError(error);
      }
    }
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to upload document');
  }

  return response.json();
}

export async function listDocuments(): Promise<Document[]> {
  const response = await fetch(`${API_BASE_URL}/documents`);

  if (!response.ok) {
    throw new Error('Failed to retrieve document inventory');
  }

  const data = await response.json();
  return data.documents || [];
}

export async function deleteDocument(documentId: string): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentId)}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to delete document');
  }

  return response.json();
}

// --- Session APIs ---

export async function listSessions(): Promise<Session[]> {
  const response = await fetch(`${API_BASE_URL}/sessions`);
  if (!response.ok) {
    throw new Error('Failed to list sessions');
  }
  const data = await response.json();
  return data.sessions || [];
}

export async function createSession(id: string, name: string): Promise<Session> {
  const response = await fetch(`${API_BASE_URL}/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ id, name }),
  });
  if (!response.ok) {
    throw new Error('Failed to create session');
  }
  const data = await response.json();
  return data.session;
}

export async function getSessionHistory(sessionId: string): Promise<ChatMessage[]> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/history`);
  if (!response.ok) {
    throw new Error('Failed to fetch session history');
  }
  const data = await response.json();
  return data.history || [];
}

export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete session');
  }
}

export interface SentimentTimelineItem {
  date: string;
  source: string;
  hawk_score: number;
  dove_score: number;
  net_stance: number;
}

export async function getSentimentTimeline(): Promise<SentimentTimelineItem[]> {
  const response = await fetch(`${API_BASE_URL}/sentiment-timeline`);
  if (!response.ok) {
    throw new Error('Failed to fetch sentiment timeline');
  }
  return response.json();
}
