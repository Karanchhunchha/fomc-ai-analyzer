import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.API_BASE_URL || "http://localhost:8000";
const API_KEY = process.env.INTERNAL_API_KEY || "";

export async function GET(request: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  return handleRequest(request, params);
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  return handleRequest(request, params);
}

export async function DELETE(request: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  return handleRequest(request, params);
}

async function handleRequest(request: NextRequest, paramsPromise: Promise<{ path?: string[] }>) {
  try {
    const { path } = await paramsPromise;
    const subPath = path ? path.join("/") : "";
    const searchParams = request.nextUrl.search;
    const targetUrl = `${BACKEND_URL}/${subPath}${searchParams}`;

    // Forward headers, but make sure to append API Key
    const headers = new Headers();
    request.headers.forEach((value, key) => {
      // Avoid forwarding host and other problematic headers
      if (!["host", "connection", "content-length"].includes(key.toLowerCase())) {
        headers.set(key, value);
      }
    });

    if (API_KEY) {
      headers.set("X-API-Key", API_KEY);
    }

    const method = request.method;
    let body: any = null;

    if (method !== "GET" && method !== "HEAD") {
      // For POST/DELETE, forward request body exactly as-is using raw bytes
      body = await request.arrayBuffer();
      headers.set("content-length", body.byteLength.toString());
    }

    const response = await fetch(targetUrl, {
      method,
      headers,
      body,
    });

    const isSse = response.headers.get("content-type")?.includes("text/event-stream");

    if (isSse && response.body) {
      // Pipe stream directly for SSE (disable buffering for long-running synthesis)
      return new NextResponse(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: {
          "Content-Type": "text/event-stream; charset=utf-8",
          "Cache-Control": "no-cache, no-transform",
          "Connection": "keep-alive",
          "X-Accel-Buffering": "no",
        },
      });
    }

    // Otherwise return normal response
    const responseHeaders = new Headers();
    response.headers.forEach((value, key) => {
      if (!["transfer-encoding", "content-encoding", "content-length"].includes(key.toLowerCase())) {
        responseHeaders.set(key, value);
      }
    });

    const resBody = await response.arrayBuffer();

    return new NextResponse(resBody, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error: any) {
    console.error("Global proxy error:", error);
    return NextResponse.json(
      { error: "GLOBAL_PROXY_ERROR", message: error.message, stack: error.stack },
      { status: 500 }
    );
  }
}
