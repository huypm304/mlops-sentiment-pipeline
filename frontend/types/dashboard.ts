import type { ReactNode } from "react"

export type StatCardData = {
  title: string
  value: string | number
  description?: string
  icon?: ReactNode
  trend?: { value: string; positive?: boolean }
  accent?: "default" | "cyan" | "emerald" | "amber"
}

export type PageHeaderProps = {
  title: string
  description?: string
  actions?: ReactNode
  eyebrow?: string
}

export type AspectSpan = {
  aspect: string
  target: string
  sentiment: "positive" | "negative" | "neutral"
  confidence: number
  start: number
  end: number
}

export type AbsaAspect = {
  aspect: string
  target: string
  sentiment: "positive" | "negative" | "neutral"
  confidence: number
}

export type InferenceResult = {
  globalSentiment: "positive" | "negative" | "neutral"
  globalConfidence: number
  aspects: AbsaAspect[]
  spans: AspectSpan[]
  latencyMs: number
}
