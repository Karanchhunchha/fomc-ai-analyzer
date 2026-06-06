"use client"
import React from "react"
import { BorderBeam } from "@/components/ui/border-beam"
import { NumberTicker } from "@/components/ui/number-ticker"
import { ShieldCheck, Cpu, HardDrive, Database } from "lucide-react"

interface TopbarProps {
  docCount: number
  cacheCount: number
  isBackendLive: boolean
  model: string
}

export function Topbar({ docCount, cacheCount, isBackendLive, model }: TopbarProps) {
  return (
    <header className="relative h-12 flex items-center justify-between px-6 bg-term-bg-panel border-b border-term-border overflow-hidden select-none">
      {/* Brand & Logo */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <div className="h-5 w-5 rounded bg-gradient-to-tr from-term-accent-blue to-term-hawkish-green flex items-center justify-center shadow-md">
            <span className="text-[10px] font-bold text-term-bg-deep">F</span>
          </div>
          <span className="font-display font-semibold text-xs tracking-wider uppercase text-term-text-primary">
            FOMC <span className="text-term-accent-blue">Research Terminal</span>
          </span>
        </div>

        {/* Real-time status indicators */}
        <div className="h-4 w-[1px] bg-term-border" />
        
        <div className="flex items-center space-x-2">
          {/* Connection status */}
          <span className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono border ${
            isBackendLive 
              ? "bg-term-hawkish-green/5 border-term-hawkish-green/20 text-term-hawkish-green" 
              : "bg-term-dovish-red/5 border-term-dovish-red/20 text-term-dovish-red"
          }`}>
            <span className={`h-1.5 w-1.5 rounded-full ${isBackendLive ? "bg-term-hawkish-green animate-pulse" : "bg-term-dovish-red"}`} />
            <span>{isBackendLive ? "API LIVE" : "DISCONNECTED"}</span>
          </span>

          {/* Database stats */}
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono border bg-term-bg-card border-term-border text-term-text-secondary">
            <Database className="h-3 w-3 text-term-accent-blue" />
            <span>DOCS:</span>
            <span className="text-term-text-primary font-bold">
              {docCount > 0 ? <NumberTicker value={docCount} /> : 0}
            </span>
          </span>

          {/* Cache stats */}
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono border bg-term-bg-card border-term-border text-term-text-secondary">
            <HardDrive className="h-3 w-3 text-term-alert-amber" />
            <span>CACHE:</span>
            <span className="text-term-text-primary font-bold">
              {cacheCount > 0 ? <NumberTicker value={cacheCount} /> : 0}
            </span>
          </span>
        </div>
      </div>

      {/* Model & Security readout */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-1.5 px-3 py-1 bg-term-bg-card border border-term-border rounded text-[10px] font-mono text-term-text-secondary font-medium">
          <Cpu className="h-3.5 w-3.5 text-term-accent-blue shrink-0" />
          <span>{model}</span>
        </div>
        <div className="flex items-center space-x-1 text-[10px] font-mono text-term-hawkish-green/80 bg-term-hawkish-green/5 border border-term-hawkish-green/15 px-2 py-0.5 rounded">
          <ShieldCheck className="h-3 w-3" />
          <span>SECURE</span>
        </div>
      </div>

      {/* Under-line premium animation from 21st.dev */}
      <BorderBeam
        size={250}
        duration={6}
        colorFrom="var(--term-accent-blue)"
        colorTo="var(--term-hawkish-green)"
        className="absolute bottom-0 left-0"
      />
    </header>
  )
}
