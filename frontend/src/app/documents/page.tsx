import React from "react";

export default function DocumentsPage() {
  return (
    <div className="flex h-screen bg-[#09090b] text-white overflow-hidden items-center justify-center">
      <div className="text-center space-y-4 max-w-md">
        <h1 className="text-4xl font-playfair tracking-tight text-white/90">
          Document Intelligence
        </h1>
        <p className="text-white/50 font-inter text-sm leading-relaxed">
          The ingestion pipeline and semantic indexer are running. Historical FOMC minutes are being processed and stored in the vector database.
        </p>
        <div className="pt-8">
          <div className="w-16 h-1 bg-amber-500/20 mx-auto rounded-full overflow-hidden">
            <div className="w-1/2 h-full bg-amber-500/80 animate-[shimmer_1.5s_infinite]" />
          </div>
        </div>
      </div>
    </div>
  );
}
