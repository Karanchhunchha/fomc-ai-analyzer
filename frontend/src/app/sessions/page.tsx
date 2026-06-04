import React from "react";

export default function SessionsPage() {
  return (
    <div className="flex h-screen bg-[#09090b] text-white overflow-hidden items-center justify-center">
      <div className="text-center space-y-4 max-w-md">
        <h1 className="text-4xl font-playfair tracking-tight text-white/90">
          Research History
        </h1>
        <p className="text-white/50 font-inter text-sm leading-relaxed">
          Access your past semantic queries and grounded research sessions.
        </p>
      </div>
    </div>
  );
}
