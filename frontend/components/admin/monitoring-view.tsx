"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import { ArrowRight, Loader2, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { fetchAnalytics } from "@/lib/api/analytics"
import { fetchMonitoring, type MonitoringPayload } from "@/lib/api/runtime"
import { cn } from "@/lib/utils"

const P95_TARGET_MS = 1500
const DRIFT_THRESHOLD = 0.18

type DriftSignalStatus = "Normal" | "Warning" | "Review recommended" | "Stable"

function OpsMetric({
  label,
  value,
  meta,
  ok,
}: {
  label: string
  value: string
  meta?: string
  ok?: boolean
}) {
  return (
    <div className="rounded-md border border-border/60 bg-card px-3 py-2.5">
      <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p
        className={cn(
          "mt-1 font-mono text-[15px] font-semibold tabular-nums",
          ok === true && "text-emerald-400",
          ok === false && "text-amber-400",
        )}
      >
        {value}
      </p>
      {meta ? <p className="mt-0.5 text-[10px] text-muted-foreground">{meta}</p> : null}
    </div>
  )
}

function GuardrailBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    PASS: "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20",
    WARN: "bg-amber-500/10 text-amber-400 ring-amber-500/20",
    REVIEW: "bg-blue-500/10 text-blue-400 ring-blue-500/20",
    REJECT: "bg-red-500/10 text-red-400 ring-red-500/20",
  }
  return (
    <span
      className={cn(
        "inline-flex rounded px-1.5 py-0.5 text-[10px] font-semibold ring-1 ring-inset",
        styles[status] ?? "bg-muted text-muted-foreground ring-border",
      )}
    >
      {status}
    </span>
  )
}

function driftLabel(value: number, threshold = DRIFT_THRESHOLD): DriftSignalStatus {
  if (value >= threshold) return "Warning"
  return "Normal"
}

function formatPrediction(sentiment: string, aspects: string[]): string {
  const label = sentiment.charAt(0).toUpperCase() + sentiment.slice(1)
  if (aspects.length === 0) return `${label} · no aspects`
  return `${label} · ${aspects.slice(0, 2).join(", ")}${aspects.length > 2 ? "…" : ""}`
}

export function MonitoringView() {
  const [monitoring, setMonitoring] = useState<MonitoringPayload | null>(null)
  const [analytics, setAnalytics] = useState<Awaited<ReturnType<typeof fetchAnalytics>> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    setError(null)
    try {
      const [mon, ana] = await Promise.all([
        fetchMonitoring(),
        fetchAnalytics(24).catch(() => null),
      ])
      setMonitoring(mon)
      setAnalytics(ana)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load monitoring")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(() => load(true), 30_000)
    return () => clearInterval(id)
  }, [load])

  const drift = monitoring?.drift
  const summary = analytics?.summary

  const driftSignals = useMemo(() => {
    if (!drift || drift.status === "insufficient_data") {
      return {
        aspect: "Normal" as DriftSignalStatus,
        sentiment: "Normal" as DriftSignalStatus,
        textLength: "Normal" as DriftSignalStatus,
        overall: "Stable" as DriftSignalStatus,
      }
    }
    const overall: DriftSignalStatus = drift.suggest_retrain ? "Review recommended" : "Stable"
    return {
      aspect: driftLabel(drift.aspect_drift),
      sentiment: driftLabel(drift.sentiment_drift),
      textLength: "Normal" as DriftSignalStatus,
      overall,
    }
  }, [drift])

  const showBehaviorAlert =
    drift &&
    drift.status !== "insufficient_data" &&
    (drift.suggest_retrain || drift.status === "alert" || drift.status === "warning")

  if (loading && !monitoring) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading monitoring…
      </div>
    )
  }

  if (error && !monitoring) {
    return <EmptyState title="Monitoring unavailable" description={error} />
  }

  if (!monitoring) return null

  const healthy = monitoring.endpoint_health === "healthy"
  const lowConfRate = summary?.low_confidence_rate ?? 0
  const lowConfThreshold = summary?.low_confidence_threshold_pct ?? 32
  const predictions24h = summary?.predictions ?? monitoring.request_volume_total
  const pending = summary?.review_queue_pending ?? summary?.review_queue ?? 0
  const urgent = summary?.review_queue_urgent ?? summary?.review_queue ?? 0
  const p95 = monitoring.p95_latency_ms
  const recent = analytics?.recent_predictions ?? []

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-border/50 pb-3">
        <div>
          <h1 className="text-[15px] font-semibold tracking-tight">Monitoring</h1>
          <p className="mt-0.5 max-w-2xl text-[13px] text-muted-foreground">
            Track API reliability, prediction quality, and review signals for the active production
            model.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={refreshing}
          onClick={() => load(true)}
          className="h-8 gap-1.5 text-xs"
        >
          <RefreshCw className={cn("size-3", refreshing && "animate-spin")} />
          Refresh
        </Button>
      </header>

      {showBehaviorAlert ? (
        <div className="flex flex-col gap-2 rounded-md border border-border/70 bg-muted/30 px-3 py-2.5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-[13px] font-medium">Model behavior changed</p>
            <p className="mt-0.5 text-[12px] text-muted-foreground">
              Production traffic differs from the training baseline. Review recent samples before
              starting a new training run.
            </p>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2">
            <Button size="sm" variant="outline" className="h-8 text-xs" asChild>
              <Link href="/admin/review-queue">View samples</Link>
            </Button>
            <Button size="sm" className="h-8 text-xs" asChild>
              <Link href="/admin/pipeline">Create retrain request</Link>
            </Button>
          </div>
        </div>
      ) : null}

      <section className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
        <OpsMetric
          label="API health"
          value={healthy ? "Healthy" : "Degraded"}
          meta={`${monitoring.api_status} · uptime ${Math.floor(monitoring.uptime_seconds / 60)}m`}
          ok={healthy}
        />
        <OpsMetric
          label="Predictions"
          value={String(predictions24h)}
          meta="last 24h"
        />
        <OpsMetric
          label="Low-confidence rate"
          value={`${lowConfRate.toFixed(1)}%`}
          meta={`threshold ${lowConfThreshold.toFixed(0)}%`}
          ok={lowConfRate < lowConfThreshold}
        />
        <OpsMetric
          label="Review queue"
          value={`${pending} pending`}
          meta={`${urgent} urgent`}
          ok={urgent === 0}
        />
        <OpsMetric
          label="p95 latency"
          value={`${p95}ms`}
          meta={`target < ${P95_TARGET_MS}ms`}
          ok={p95 < P95_TARGET_MS}
        />
      </section>

      <section className="rounded-md border border-border/60 bg-card">
        <div className="flex items-center justify-between border-b border-border/50 px-3 py-2">
          <p className="text-[12px] font-medium">Drift signals</p>
          <span className="font-mono text-[10px] text-muted-foreground">
            baseline n={drift?.baseline?.sample_size ?? 0} · live n=
            {drift?.production_sample_size ?? drift?.production?.sample_size ?? 0}
          </span>
        </div>
        <dl className="grid gap-px bg-border/40 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Aspect distribution", value: driftSignals.aspect },
            { label: "Sentiment distribution", value: driftSignals.sentiment },
            { label: "Text length", value: driftSignals.textLength },
            { label: "Overall", value: driftSignals.overall },
          ].map((row) => (
            <div key={row.label} className="bg-card px-3 py-2.5">
              <dt className="text-[10px] text-muted-foreground">{row.label}</dt>
              <dd
                className={cn(
                  "mt-0.5 text-[13px] font-medium",
                  row.value === "Warning" && "text-amber-400",
                  row.value === "Review recommended" && "text-amber-400",
                  row.value === "Normal" && "text-foreground",
                  row.value === "Stable" && "text-emerald-400",
                )}
              >
                {row.value}
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="rounded-md border border-border/60 bg-card">
        <div className="flex items-center justify-between border-b border-border/50 px-3 py-2">
          <div>
            <p className="text-[12px] font-medium">Recent predictions</p>
            <p className="text-[10px] text-muted-foreground">
              Production request log · absa-v1
            </p>
          </div>
          <Button variant="ghost" size="sm" className="h-7 text-xs" asChild>
            <Link href="/admin/review-queue">
              Open queue
              <ArrowRight className="ml-1 size-3" />
            </Link>
          </Button>
        </div>

        {recent.length === 0 ? (
          <div className="px-3 py-8">
            <EmptyState
              title="No predictions logged"
              description="Use Operations → Inference to run a test request. Results appear here automatically."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-[12px]">
              <thead>
                <tr className="border-b border-border/40 text-[10px] text-muted-foreground">
                  <th className="px-3 py-2 text-left font-medium">Time</th>
                  <th className="px-3 py-2 text-left font-medium">Text</th>
                  <th className="px-3 py-2 text-left font-medium">Prediction</th>
                  <th className="px-3 py-2 text-right font-medium">Confidence</th>
                  <th className="px-3 py-2 text-left font-medium">Guardrail</th>
                  <th className="px-3 py-2 text-left font-medium">Model</th>
                  <th className="px-3 py-2 text-left font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {recent.slice(0, 12).map((row, idx) => {
                  const needsReview = row.guardrail === "REVIEW" || row.guardrail === "WARN"
                  return (
                    <tr key={`${row.time}-${idx}`} className="border-b border-border/20 last:border-0">
                      <td className="whitespace-nowrap px-3 py-2 font-mono text-[11px] text-muted-foreground">
                        {row.time}
                      </td>
                      <td className="max-w-[220px] truncate px-3 py-2" title={row.text}>
                        {row.text}
                      </td>
                      <td className="whitespace-nowrap px-3 py-2 text-muted-foreground">
                        {formatPrediction(row.sentiment, row.aspects)}
                      </td>
                      <td className="px-3 py-2 text-right font-mono tabular-nums">
                        {(row.confidence * 100).toFixed(0)}%
                      </td>
                      <td className="px-3 py-2">
                        <GuardrailBadge status={row.guardrail} />
                      </td>
                      <td className="px-3 py-2 font-mono text-[11px] text-muted-foreground">
                        {row.model_version}
                      </td>
                      <td className="px-3 py-2">
                        {needsReview ? (
                          <Link
                            href="/admin/review-queue"
                            className="text-[11px] font-medium text-primary hover:underline"
                          >
                            Review
                          </Link>
                        ) : (
                          <span className="text-muted-foreground/50">—</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <p className="text-[10px] text-muted-foreground">
        Refreshed {new Date().toLocaleTimeString()} · error rate {monitoring.error_rate_pct}% · avg{" "}
        {monitoring.avg_latency_ms}ms
      </p>
    </div>
  )
}
