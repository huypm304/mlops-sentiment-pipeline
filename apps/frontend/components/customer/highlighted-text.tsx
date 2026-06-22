"use client"

import type { ReactNode } from "react"

import { cn } from "@/lib/utils"
import type { AspectSpan } from "@/types/dashboard"

const spanStyles = {
  positive: "bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/25",
  negative: "bg-red-500/15 text-red-400 ring-1 ring-red-500/25",
  neutral: "bg-white/10 text-foreground ring-1 ring-white/15",
} as const

type HighlightedTextProps = {
  text: string
  spans: AspectSpan[]
  className?: string
}

export function HighlightedText({ text, spans, className }: HighlightedTextProps) {
  if (!spans.length) {
    return (
      <p className={cn("text-sm leading-relaxed text-foreground", className)}>
        {text}
      </p>
    )
  }

  const sorted = [...spans].sort((a, b) => a.start - b.start)
  const segments: ReactNode[] = []
  let cursor = 0

  sorted.forEach((span, i) => {
    if (span.start > cursor) {
      segments.push(
        <span key={`p-${i}`} className="text-muted-foreground">
          {text.slice(cursor, span.start)}
        </span>
      )
    }
    segments.push(
      <mark
        key={`s-${i}`}
        title={`${span.aspect.replace("#", " · ")}`}
        className={cn("rounded px-0.5", spanStyles[span.sentiment])}
      >
        {text.slice(span.start, span.end)}
      </mark>
    )
    cursor = span.end
  })

  if (cursor < text.length) {
    segments.push(
      <span key="tail" className="text-muted-foreground">
        {text.slice(cursor)}
      </span>
    )
  }

  return (
    <p className={cn("text-sm leading-relaxed", className)}>{segments}</p>
  )
}
