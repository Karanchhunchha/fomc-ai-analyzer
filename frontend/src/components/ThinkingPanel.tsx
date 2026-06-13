"use client"
import React, { useState } from "react"
import { ChevronDown, ChevronRight, CheckCircle2, CircleDashed, Loader2 } from "lucide-react"

export interface ThinkingStep {
  step: string
  message: string
}

interface ThinkingPanelProps {
  steps: ThinkingStep[]
  isStreaming: boolean
}

export function ThinkingPanel({ steps, isStreaming }: ThinkingPanelProps) {
  const [isOpen, setIsOpen] = useState(true)

  if (steps.length === 0 && !isStreaming) return null

  // The sequence of expected steps
  const expectedSteps = [
    { id: "classified", label: "Classifying query intent" },
    { id: "retrieved", label: "Retrieving semantic evidence" },
    { id: "reranked", label: "Reranking context with CrossEncoder" },
    { id: "validated", label: "Validating citations" },
    { id: "streamed", label: "Streaming response" },
  ]

  // Map received steps to our expected UI list
  const completedStepIds = steps.map((s) => s.step)
  
  // Find the currently active step (the first expected step that hasn't completed yet)
  const activeStepIdx = expectedSteps.findIndex(s => !completedStepIds.includes(s.id))

  return (
    <div className="bg-term-bg-deep border border-term-border rounded-lg overflow-hidden select-none animate-fade-in mt-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-2 hover:bg-term-bg-hover/30 transition-colors"
      >
        <div className="flex items-center space-x-2">
          {isStreaming ? (
            <Loader2 className="w-3.5 h-3.5 text-term-accent-blue animate-spin" />
          ) : (
            <CheckCircle2 className="w-3.5 h-3.5 text-term-hawkish-green" />
          )}
          <span className="text-[11px] font-mono font-medium text-term-text-secondary uppercase tracking-widest">
            {isStreaming ? "AI Agent Thinking..." : "Thinking Process Complete"}
          </span>
        </div>
        {isOpen ? (
          <ChevronDown className="w-4 h-4 text-term-text-muted" />
        ) : (
          <ChevronRight className="w-4 h-4 text-term-text-muted" />
        )}
      </button>

      {isOpen && (
        <div className="px-4 py-3 border-t border-term-border/50 bg-term-bg-deep/40">
          <ul className="space-y-2">
            {expectedSteps.map((step, idx) => {
              const isCompleted = completedStepIds.includes(step.id)
              const isActive = isStreaming && idx === activeStepIdx
              const isPending = !isCompleted && !isActive

              // Find the actual message if completed
              const stepData = steps.find(s => s.step === step.id)
              const displayLabel = stepData ? stepData.message : step.label

              return (
                <li key={step.id} className="flex items-start space-x-2.5">
                  <div className="mt-0.5">
                    {isCompleted ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-term-hawkish-green" />
                    ) : isActive ? (
                      <Loader2 className="w-3.5 h-3.5 text-term-accent-blue animate-spin" />
                    ) : (
                      <CircleDashed className="w-3.5 h-3.5 text-term-text-muted opacity-50" />
                    )}
                  </div>
                  <span
                    className={`text-[11px] font-mono ${
                      isCompleted
                        ? "text-term-text-primary font-medium"
                        : isActive
                        ? "text-term-accent-blue animate-pulse"
                        : "text-term-text-muted"
                    }`}
                  >
                    {displayLabel}
                  </span>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}
