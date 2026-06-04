import React from "react";

export default function ComparePage() {
  return (
    <div className="flex h-screen bg-[#09090b] text-white overflow-hidden items-center justify-center">
      <div className="text-center space-y-4 max-w-md">
        <h1 className="text-4xl font-playfair tracking-tight text-white/90">
          Policy Comparison
        </h1>
        <p className="text-white/50 font-inter text-sm leading-relaxed">
          Cross-encoder reranking is active. Compare hawkish and dovish shifts across multiple FOMC meetings.
        </p>
        <div className="pt-8 flex justify-center gap-4">
          <div className="w-12 h-16 rounded border border-white/10 bg-white/5" />
          <div className="flex items-center text-amber-500/50">
             <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M7 11V7a5 5 0 0 1 10 0v4"></path><path d="M11 16h2"></path><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect></svg>
          </div>
          <div className="w-12 h-16 rounded border border-white/10 bg-white/5" />
        </div>
      </div>
    </div>
  );
}
