"use client"

import { useState } from "react"
import { AlertCircle, Loader2 } from "lucide-react"

import { HighlightedText } from "@/components/customer/highlighted-text"
import { Button } from "@/components/ui/button"
import { predictReview } from "@/lib/api/predict"
import type { InferenceResult } from "@/types/dashboard"

const sentimentLabel = {
  positive: "Positive",
  negative: "Negative",
  neutral: "Neutral",
} as const

type ReviewAnalyzerProps = {
  onAnalyzed?: (result: InferenceResult, text: string) => void
}

export function ReviewAnalyzer({ onAnalyzed }: ReviewAnalyzerProps) {
  const [text, setText] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<InferenceResult | null>(null)

  async function analyze() {
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await predictReview(text.trim())
      setResult(res)
      onAnalyzed?.(res, text)
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Inference failed. Is the API running on port 8000?"
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-white/[0.08] bg-white/[0.02] p-4">
        <label className="text-xs font-medium text-muted-foreground">
          Customer review
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={4}
          className="mt-2 w-full resize-none rounded-md border border-white/[0.08] bg-background p-3 text-sm leading-relaxed focus:outline-none focus:ring-1 focus:ring-primary/40"
          placeholder="Paste a Vietnamese product review…"
        />
        <div className="mt-3 flex justify-end">
          <Button size="sm" disabled={loading || !text.trim()} onClick={analyze}>
            {loading ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Analyzing…
              </>
            ) : (
              "Analyze review"
            )}
          </Button>
        </div>
      </div>

      {error ? (
        <div className="flex items-start gap-2 rounded-lg border border-red-500/20 bg-red-500/5 p-3 text-sm text-red-400">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          <p>{error}</p>
        </div>
      ) : null}

      {result ? (
        <div className="rounded-lg border border-white/[0.08] bg-white/[0.02] p-4">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted-foreground">Overall</span>
            <span className="rounded-md bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
              {sentimentLabel[result.globalSentiment]}
            </span>
            <span className="text-xs text-muted-foreground">
              {(result.globalConfidence * 100).toFixed(0)}% confidence
            </span>
            <span className="text-xs text-muted-foreground">
              {result.aspects.length} aspects · {result.latencyMs}ms
            </span>
          </div>
          <HighlightedText text={text} spans={result.spans} />
          <ul className="mt-4 space-y-2 border-t border-white/[0.06] pt-4">
            {result.aspects.map((a) => (
              <li
                key={`${a.aspect}-${a.target}`}
                className="flex justify-between gap-2 text-xs"
              >
                <span>
                  <span className="font-medium text-foreground">{a.target}</span>
                  <span className="ml-2 text-muted-foreground">{a.aspect}</span>
                </span>
                <span className="shrink-0 text-muted-foreground">
                  <span className="capitalize">{a.sentiment}</span>
                  <span className="ml-2 tabular-nums">
                    {(a.confidence * 100).toFixed(0)}%
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  )
}

