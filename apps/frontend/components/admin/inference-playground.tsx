"use client"

import { useEffect, useState } from "react"
import { AlertCircle, CheckCircle2, Loader2, ShieldAlert, ShieldCheck, ShieldX } from "lucide-react"
import type { LucideIcon } from "lucide-react"

import { HighlightedText } from "@/components/customer/highlighted-text"
import { Button } from "@/components/ui/button"
import { fetchModels } from "@/lib/api/metrics"
import { predictReview } from "@/lib/api/predict"
import { evaluateGuardrail, type GuardrailStatus } from "@/lib/guardrails"
import type { InferenceResult } from "@/types/dashboard"
import { cn } from "@/lib/utils"

function deriveGuardrail(result: InferenceResult): {
  status: GuardrailStatus
  reasons: string[]
} {
  return evaluateGuardrail(result)
}

const GUARDRAIL_CONFIG: Record<
  GuardrailStatus,
  { label: string; className: string; icon: LucideIcon }
> = {
  PASS: {
    label: "PASS",
    className: "bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/25",
    icon: ShieldCheck,
  },
  WARN: {
    label: "WARN",
    className: "bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/25",
    icon: ShieldAlert,
  },
  REVIEW: {
    label: "REVIEW",
    className: "bg-blue-500/10 text-blue-400 ring-1 ring-blue-500/25",
    icon: ShieldAlert,
  },
  REJECT: {
    label: "REJECT",
    className: "bg-red-500/10 text-red-400 ring-1 ring-red-500/25",
    icon: ShieldX,
  },
}

const SENTIMENT_STYLES = {
  positive: "bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/25",
  negative: "bg-red-500/10 text-red-400 ring-1 ring-red-500/25",
  neutral: "bg-muted/60 text-muted-foreground ring-1 ring-border",
}

export function InferencePlayground() {
  const [text, setText] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<InferenceResult | null>(null)
  const [guardrail, setGuardrail] = useState<ReturnType<typeof deriveGuardrail> | null>(null)
  const [models, setModels] = useState<{ version: string; status: string }[]>([])

  useEffect(() => {
    fetchModels()
      .then(setModels)
      .catch(() => setModels([]))
  }, [])

  async function predict() {
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    setGuardrail(null)
    try {
      const res = await predictReview(text.trim())
      setResult(res)
      setGuardrail(deriveGuardrail(res))
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Inference failed. Is the API running on port 8000?",
      )
    } finally {
      setLoading(false)
    }
  }

  const productionModel =
    result?.modelVersion ??
    models.find((m) => m.status === "production")?.version ??
    models[0]?.version ??
    "—"

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_380px]">
      <div className="space-y-3">
        <div className="rounded-lg border border-border/60 bg-card">
          <div className="flex items-center justify-between gap-2 border-b border-border/40 px-4 py-2.5">
            <p className="text-[12px] font-medium">Input</p>
            <span className="font-mono text-[11px] text-muted-foreground">
              {productionModel}
            </span>
          </div>
          <div className="p-4">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={5}
              className="w-full resize-none rounded-md border border-border/60 bg-background p-3 text-sm leading-relaxed text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="Paste a Vietnamese product review here…"
            />
            <div className="mt-3 flex justify-end">
              <Button
                size="sm"
                className="h-8"
                disabled={loading || !text.trim()}
                onClick={predict}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                    Predicting…
                  </>
                ) : (
                  "Run inference"
                )}
              </Button>
            </div>
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-2 rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        {result && (
          <div className="rounded-lg border border-border/60 bg-card">
            <div className="border-b border-border/40 px-4 py-2.5">
              <p className="text-[12px] font-medium">Highlighted spans</p>
            </div>
            <div className="p-4">
              <HighlightedText text={text} spans={result.spans} />
            </div>
          </div>
        )}

        {result && (
          <div className="rounded-lg border border-border/60 bg-card">
            <div className="border-b border-border/40 px-4 py-2.5">
              <p className="text-[12px] font-medium">Aspect opinions</p>
            </div>
            {result.aspects.length === 0 ? (
              <p className="px-4 py-4 text-sm text-muted-foreground/60">
                No aspect opinions extracted.
              </p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border/30 text-[11px] text-muted-foreground">
                    <th className="px-4 py-2 text-left font-medium">Target span</th>
                    <th className="px-4 py-2 text-left font-medium">Aspect</th>
                    <th className="px-4 py-2 text-left font-medium">Sentiment</th>
                    <th className="px-4 py-2 text-right font-medium">Raw conf.</th>
                    <th className="px-4 py-2 text-right font-medium">Calibrated</th>
                  </tr>
                </thead>
                <tbody>
                  {result.aspects.map((a, i) => (
                    <tr
                      key={i}
                      className="border-b border-border/20 last:border-0 hover:bg-muted/20 transition-colors"
                    >
                      <td className="px-4 py-2 font-mono text-[12px]">{a.target}</td>
                      <td className="px-4 py-2 text-[12px] text-muted-foreground">{a.aspect}</td>
                      <td className="px-4 py-2">
                        <span
                          className={cn(
                            "rounded px-1.5 py-0.5 text-[10px] font-medium capitalize",
                            SENTIMENT_STYLES[a.sentiment],
                          )}
                        >
                          {a.sentiment}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-right font-mono text-[12px] tabular-nums">
                        {((a.rawConfidence ?? a.confidence) * 100).toFixed(1)}%
                      </td>
                      <td className="px-4 py-2 text-right font-mono text-[12px] tabular-nums text-muted-foreground">
                        {((a.calibratedConfidence ?? a.confidence) * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      <div className="space-y-3">
        {result && guardrail ? (
          <>
            <div className="rounded-lg border border-border/60 bg-card">
              <div className="border-b border-border/40 px-4 py-2.5">
                <p className="text-[12px] font-medium">Global result</p>
              </div>
              <div className="divide-y divide-border/30">
                <Row label="Model version">
                  <span className="font-mono text-[12px]">{productionModel}</span>
                </Row>
                <Row label="Global sentiment">
                  <span
                    className={cn(
                      "rounded px-1.5 py-0.5 text-[10px] font-medium capitalize",
                      SENTIMENT_STYLES[result.globalSentiment],
                    )}
                  >
                    {result.globalSentiment}
                  </span>
                </Row>
                <Row label="Raw confidence">
                  <span className="font-mono text-[12px] tabular-nums">
                    {((result.globalRawConfidence ?? result.globalConfidence) * 100).toFixed(1)}%
                  </span>
                </Row>
                <Row label="Calibrated confidence">
                  <span className="font-mono text-[12px] tabular-nums text-muted-foreground">
                    {(result.globalConfidence * 100).toFixed(1)}%
                  </span>
                </Row>
                <Row label="Aspects extracted">
                  <span className="font-mono text-[12px] tabular-nums">
                    {result.aspects.length}
                  </span>
                </Row>
                <Row label="Latency">
                  <span className="font-mono text-[12px] tabular-nums">
                    {result.latencyMs} ms
                  </span>
                </Row>
              </div>
            </div>

            <div
              className={cn(
                "rounded-lg border p-4",
                guardrail.status === "PASS" && "border-emerald-500/20 bg-emerald-500/[0.04]",
                guardrail.status === "WARN" && "border-amber-500/20 bg-amber-500/[0.04]",
                guardrail.status === "REVIEW" && "border-blue-500/20 bg-blue-500/[0.04]",
                guardrail.status === "REJECT" && "border-red-500/20 bg-red-500/[0.04]",
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="text-[12px] font-medium">Guardrail</p>
                {(() => {
                  const cfg = GUARDRAIL_CONFIG[guardrail.status]
                  const Icon = cfg.icon
                  return (
                    <span
                      className={cn(
                        "flex items-center gap-1 rounded px-2 py-0.5 text-[11px] font-semibold",
                        cfg.className,
                      )}
                    >
                      <Icon className="size-3" />
                      {cfg.label}
                    </span>
                  )
                })()}
              </div>

              {guardrail.status === "PASS" ? (
                <div className="mt-3 flex items-center gap-2 text-[12px] text-emerald-400">
                  <CheckCircle2 className="size-3.5 shrink-0" />
                  Prediction meets confidence thresholds.
                </div>
              ) : (
                <ul className="mt-3 space-y-1">
                  {guardrail.reasons.map((r, i) => (
                    <li key={i} className="flex items-start gap-2 text-[11px] text-muted-foreground">
                      <span className="mt-0.5 size-1 shrink-0 rounded-full bg-current opacity-50" />
                      {r}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        ) : (
          <div className="rounded-lg border border-dashed border-border/60 bg-muted/10 px-4 py-10 text-center text-sm text-muted-foreground">
            Run inference to see results
          </div>
        )}
      </div>
    </div>
  )
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2.5">
      <span className="text-[11px] text-muted-foreground">{label}</span>
      <span>{children}</span>
    </div>
  )
}
