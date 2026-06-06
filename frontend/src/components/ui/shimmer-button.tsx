"use client"

import React from "react"
import { cn } from "@/lib/utils"

interface ShimmerButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  shimmerColor?: string
  background?: string
  borderRadius?: string
}

export const ShimmerButton = React.forwardRef<HTMLButtonElement, ShimmerButtonProps>(
  (
    {
      shimmerColor = "#3B82F6",
      background = "rgba(21, 21, 31, 1)",
      borderRadius = "6px",
      className,
      children,
      ...props
    },
    ref,
  ) => {
    return (
      <button
        style={{
          borderRadius,
          background,
        }}
        className={cn(
          "relative overflow-hidden group flex items-center justify-center transition-all duration-200 active:scale-[0.98]",
          "before:absolute before:inset-0 before:w-[200%] before:h-full before:bg-[linear-gradient(90deg,transparent_0%,rgba(255,255,255,0.08)_50%,transparent_100%)] before:-left-full before:animate-[shimmer_3s_infinite_linear]",
          className
        )}
        ref={ref}
        {...props}
      >
        {/* Border glow */}
        <div
          className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none border"
          style={{
            borderColor: `${shimmerColor}40`,
            borderRadius,
          }}
        />
        {/* Content */}
        <div className="relative z-10 flex items-center justify-center w-full h-full">
          {children}
        </div>
      </button>
    )
  }
)
ShimmerButton.displayName = "ShimmerButton"
