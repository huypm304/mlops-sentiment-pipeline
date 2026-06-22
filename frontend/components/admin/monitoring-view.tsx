"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import { AlertTriangle, Loader2, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import {
  fetchAnalytics,
  fetchReviewQueue,
  type ReviewQueueItem,
} from "@/lib/api/analytics"
import { fetchModels } from "@/lib/api/metrics"
import { fetchPlatformContext, type PlatformContext } from "@/lib/api/platform"
import { formatShortDate } from "@/lib/console/format"
import { fetchMonitoring, type MonitoringPayload } from "@/lib/api/runtime"
import { cn } from "@/lib/utils"

const P95_TARGET_MS = 1500
const DRIFT_THRESHOLD = 0.18
const LOW_CONF_THRESHOLD = 30

type SignalBadgeStatus = "NORMAL" | "WARNING" | "CRITICAL"

type PredictionRow = {
  time: string
  predictionId: string
  text: string
  prediction: string
  confidence: number
  guardrail: "PASS" | "WARN" | "REVIEW" | "REJECT"
  model: string
}

type ReviewSnapshotRow = {
  requestId: string
  reason: string
  priority: "LOW" | "MEDIUM" | "HIGH"
  created: string
  status: "OPEN" | "IN_PROGRESS" | "CLOSED"
}

function StatusBadge({
  status,
  variant = "neutral",
}: {
  status: string
  variant?: "neutral" | "production" | "warning" | "signal"
}) {
  const styles: Record<string, string> = {
    PRODUCTION: "bg-muted text-foreground ring-border",
    "REVIEW RECOMMENDED": "bg-muted text-foreground ring-border",
    NORMAL: "bg-muted text-muted-foreground ring-border",
    WARNING: "bg-muted text-foreground ring-border",
    CRITICAL: "bg-muted text-foreground ring-border",
    PASS: "bg-muted text-muted-foreground ring-border",
    WARN: "bg-muted text-foreground ring-border",
    REVIEW: "bg-muted text-foreground ring-border",
    REJECT: "bg-muted text-foreground ring-border",
    LOW: "bg-muted text-muted-foreground ring-border",
    MEDIUM: "bg-muted text-foreground ring-border",
    HIGH: "bg-muted text-foreground ring-border",
    OPEN: "bg-muted text-foreground ring-border",
    IN_PROGRESS: "bg-muted text-foreground ring-border",
    CLOSED: "bg-muted text-muted-foreground ring-border",
  }

  return (
    <span
      className={cn(
        "inline-flex rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ring-1 ring-inset",
        styles[status] ?? "bg-muted text-muted-foreground ring-border",
        variant === "production" && "text-foreground",
        variant === "warning" && "text-foreground",
      )}
    >
      {status}
    </span>
  )
}

function OpsMetric({
  label,
  value,
  threshold,
  updatedAt,
}: {
  label: string
  value: string
  threshold?: string
  updatedAt: string
}) {
  return (
    <div className="rounded border border-border/60 bg-card px-3 py-2.5">
      <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 font-mono text-[15px] font-semibold tabular-nums text-foreground">
        {value}
      </p>
      {threshold ? (
        <p className="mt-0.5 text-[10px] text-muted-foreground">{threshold}</p>
      ) : null}
      <p className="mt-1 text-[10px] text-muted-foreground/70">Updated {updatedAt}</p>
    </div>
  )
}

function driftToBadge(value: number, threshold = DRIFT_THRESHOLD): SignalBadgeStatus {
  if (value >= threshold * 1.5) return "CRITICAL"
  if (value >= threshold) return "WARNING"
  return "NORMAL"
}

function overallDriftBadge(
  suggestRetrain: boolean,
  status: string | undefined,
): SignalBadgeStatus {
  if (status === "alert") return "CRITICAL"
  if (suggestRetrain || status === "warning") return "WARNING"
  return "NORMAL"
}

function formatSentimentLabel(sentiment: string): string {
  return sentiment.charAt(0).toUpperCase() + sentiment.slice(1)
}

function derivePredictionId(time: string, idx: number): string {
  const digits = time.replace(/\D/g, "").slice(-4) || String(8900 + idx)
  return `pred-${digits}`
}

function mapReviewPriority(item: ReviewQueueItem): ReviewSnapshotRow["priority"] {
  if (item.guardrail === "REJECT" || item.guardrail === "REVIEW") return "HIGH"
  if (item.guardrail === "WARN") return "MEDIUM"
  return "LOW"
}

function mapReviewStatus(status: string): ReviewSnapshotRow["status"] {
  const normalized = status.toLowerCase()
  if (normalized.includes("progress") || normalized.includes("review")) return "IN_PROGRESS"
  if (normalized.includes("resolved") || normalized.includes("closed")) return "CLOSED"
  return "OPEN"
}

function formatUpdatedAt(date: Date): string {
  return date.toISOString().slice(0, 16).replace("T", " ") + " UTC"
}

export function MonitoringView() {
  const [monitoring, setMonitoring] = useState<MonitoringPayload | null>(null)
  const [analytics, setAnalytics] = useState<Awaited<ReturnType<typeof fetchAnalytics>> | null>(
    null,
  )
  const [reviewItems, setReviewItems] = useState<ReviewQueueItem[]>([])
  const [platform, setPlatform] = useState<PlatformContext | null>(null)
  const [championEpoch, setChampionEpoch] = useState<number | null>(null)
  const [challengerModel, setChallengerModel] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date())

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    setError(null)
    try {
      const [mon, ana, queue, ctx, models] = await Promise.all([
        fetchMonitoring(),
        fetchAnalytics(24).catch(() => null),
        fetchReviewQueue(5).catch(() => ({ items: [], open_count: 0 })),
        fetchPlatformContext().catch(() => null),
        fetchModels().catch(() => []),
      ])
      setMonitoring(mon)
      setAnalytics(ana)
      setReviewItems(queue.items)
      setPlatform(ctx)
      const champion = models.find((m) => m.status === "production") ?? models[0]
      setChampionEpoch(champion?.epoch ?? null)
      setChallengerModel(models.find((m) => m.status === "candidate")?.version ?? null)
      setLastRefreshed(new Date())
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
  const updatedAt = formatUpdatedAt(lastRefreshed)

  const driftRows = useMemo(() => {
    const checkedAt = updatedAt
    if (!drift || drift.status === "insufficient_data") {
      return [
        { signal: "Aspect distribution", status: "NORMAL" as SignalBadgeStatus, checkedAt },
        { signal: "Sentiment distribution", status: "NORMAL" as SignalBadgeStatus, checkedAt },
        { signal: "Text length", status: "NORMAL" as SignalBadgeStatus, checkedAt },
        {
          signal: "Overall",
          status: "NORMAL" as SignalBadgeStatus,
          checkedAt,
        },
      ]
    }
    return [
      {
        signal: "Aspect distribution",
        status: driftToBadge(drift.aspect_drift),
        checkedAt,
      },
      {
        signal: "Sentiment distribution",
        status: driftToBadge(drift.sentiment_drift),
        checkedAt,
      },
      { signal: "Text length", status: "NORMAL" as SignalBadgeStatus, checkedAt },
      {
        signal: "Overall",
        status: overallDriftBadge(drift.suggest_retrain, drift.status),
        checkedAt,
      },
    ]
  }, [drift, updatedAt])

  const showBehaviorAlert =
    drift &&
    drift.status !== "insufficient_data" &&
    (drift.suggest_retrain || drift.status === "alert" || drift.status === "warning")

  const predictionRows = useMemo((): PredictionRow[] => {
    const recent = analytics?.recent_predictions ?? []
    return recent.slice(0, 12).map((row, idx) => ({
      time: row.time,
      predictionId: derivePredictionId(row.time, idx),
      text: row.text,
      prediction: formatSentimentLabel(row.sentiment),
      confidence: row.confidence,
      guardrail: row.guardrail,
      model: row.model_version || platform?.champion_model || "—",
    }))
  }, [analytics?.recent_predictions, platform?.champion_model])

  const reviewSnapshotRows = useMemo((): ReviewSnapshotRow[] => {
    return reviewItems.slice(0, 5).map((item) => ({
      requestId: item.id.startsWith("rq-") ? item.id : `rq-${item.id}`,
      reason: item.reason,
      priority: mapReviewPriority(item),
      created: item.time,
      status: mapReviewStatus(item.status),
    }))
  }, [reviewItems])

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
  const lowConfThreshold = summary?.low_confidence_threshold_pct ?? LOW_CONF_THRESHOLD
  const predictions24h = summary?.predictions ?? 0
  const pending = summary?.review_queue_pending ?? summary?.review_queue ?? 0
  const urgent = summary?.review_queue_urgent ?? 0
  const p95 = monitoring.p95_latency_ms ?? 0
  const championModel = platform?.champion_model ?? "—"
  const championDataset = platform?.active_dataset ?? "—"
  const championPromoted = formatShortDate(platform?.last_training_at)
  const championVersion = championEpoch != null ? `v${championEpoch}` : "—"

  return (
    <div className="space-y-4">
      <header className="border-b border-border/50 pb-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-[15px] font-semibold tracking-tight">Monitoring</h1>
              <StatusBadge status="PRODUCTION" variant="production" />
            </div>
            <p className="mt-0.5 max-w-2xl text-[13px] text-muted-foreground">
              Track API reliability, prediction quality, and review signals for the active
              production model.
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
        </div>

        <dl className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-[11px] text-muted-foreground">
          <div className="flex gap-1.5">
            <dt className="text-muted-foreground/70">Champion Model:</dt>
            <dd className="font-mono font-medium text-foreground">{championModel}</dd>
          </div>
          <div className="flex gap-1.5">
            <dt className="text-muted-foreground/70">Version:</dt>
            <dd className="font-mono font-medium text-foreground">{championVersion}</dd>
          </div>
          <div className="flex gap-1.5">
            <dt className="text-muted-foreground/70">Dataset:</dt>
            <dd className="font-mono font-medium text-foreground">{championDataset}</dd>
          </div>
          <div className="flex gap-1.5">
            <dt className="text-muted-foreground/70">Promoted:</dt>
            <dd className="font-mono font-medium text-foreground">{championPromoted}</dd>
          </div>
        </dl>
      </header>

      {showBehaviorAlert ? (
        <div className="flex flex-col gap-2 rounded border border-border/70 bg-card px-3 py-2.5 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex gap-2.5">
            <AlertTriangle className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />
            <div>
              <div className="mb-1">
                <StatusBadge status="REVIEW RECOMMENDED" variant="warning" />
              </div>
              <p className="text-[13px] font-medium">Model behavior changed</p>
              <p className="mt-0.5 text-[12px] text-muted-foreground">
                Production traffic differs from the training baseline. Review recent samples before
                starting a new training run.
              </p>
            </div>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2 sm:pt-0.5">
            <Button size="sm" variant="outline" className="h-7 text-xs" asChild>
              <Link href="/admin/review-queue">View samples</Link>
            </Button>
            <Button size="sm" variant="outline" className="h-7 text-xs" asChild>
              <Link href="/admin/pipeline">Create retrain request</Link>
            </Button>
          </div>
        </div>
      ) : null}

      <section>
        <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          Production health summary
        </p>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
          <OpsMetric
            label="API Health"
            value={healthy ? "Healthy" : "Degraded"}
            threshold={`Status: ${healthy ? "Healthy" : "Degraded"}`}
            updatedAt={updatedAt}
          />
          <OpsMetric
            label="Predictions"
            value={String(predictions24h)}
            threshold="Last 24h"
            updatedAt={updatedAt}
          />
          <OpsMetric
            label="Low-confidence rate"
            value={`${lowConfRate.toFixed(1)}%`}
            threshold={`Threshold: ${lowConfThreshold.toFixed(0)}%`}
            updatedAt={updatedAt}
          />
          <OpsMetric
            label="Review queue"
            value={`${pending} pending`}
            threshold={`${urgent} urgent`}
            updatedAt={updatedAt}
          />
          <OpsMetric
            label="p95 latency"
            value={`${p95}ms`}
            threshold={`Target: <${P95_TARGET_MS}ms`}
            updatedAt={updatedAt}
          />
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
        <section className="rounded border border-border/60 bg-card">
          <div className="border-b border-border/50 px-3 py-2">
            <p className="text-[12px] font-medium">Drift Signals</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[12px]">
              <thead>
                <tr className="border-b border-border/40 text-[10px] text-muted-foreground">
                  <th className="px-3 py-2 text-left font-medium">Signal</th>
                  <th className="px-3 py-2 text-left font-medium">Status</th>
                  <th className="px-3 py-2 text-left font-medium">Last checked</th>
                </tr>
              </thead>
              <tbody>
                {driftRows.map((row) => (
                  <tr key={row.signal} className="border-b border-border/20 last:border-0">
                    <td className="px-3 py-2 text-foreground">{row.signal}</td>
                    <td className="px-3 py-2">
                      <StatusBadge status={row.status} variant="signal" />
                    </td>
                    <td className="px-3 py-2 font-mono text-[11px] text-muted-foreground">
                      {row.checkedAt}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="rounded border border-border/60 bg-card">
          <div className="border-b border-border/50 px-3 py-2">
            <p className="text-[12px] font-medium">Model Registry Linkage</p>
          </div>
          <dl className="space-y-2.5 px-3 py-3 text-[12px]">
            <div>
              <dt className="text-[10px] uppercase tracking-wide text-muted-foreground">
                Champion Model
              </dt>
              <dd className="mt-0.5 font-mono font-medium">{championModel}</dd>
            </div>
            <div>
              <dt className="text-[10px] uppercase tracking-wide text-muted-foreground">
                Current Challenger
              </dt>
              <dd className="mt-0.5 font-mono font-medium">{challengerModel ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-[10px] uppercase tracking-wide text-muted-foreground">
                Comparison Status
              </dt>
              <dd className="mt-0.5 text-foreground">Pending evaluation</dd>
            </div>
          </dl>
          <div className="flex flex-wrap gap-2 border-t border-border/50 px-3 py-2.5">
            <Button size="sm" variant="outline" className="h-7 text-xs" asChild>
              <Link href="/admin/models">View Registry</Link>
            </Button>
            <Button size="sm" variant="outline" className="h-7 text-xs" asChild>
              <Link href="/admin/compare">Compare Models</Link>
            </Button>
          </div>
        </section>
      </div>

      <section className="rounded border border-border/60 bg-card">
        <div className="border-b border-border/50 px-3 py-2">
          <p className="text-[12px] font-medium">Recent Predictions</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[12px]">
            <thead>
              <tr className="border-b border-border/40 text-[10px] text-muted-foreground">
                <th className="px-3 py-2 text-left font-medium">Time</th>
                <th className="px-3 py-2 text-left font-medium">Prediction ID</th>
                <th className="px-3 py-2 text-left font-medium">Review Text</th>
                <th className="px-3 py-2 text-left font-medium">Prediction</th>
                <th className="px-3 py-2 text-right font-medium">Confidence</th>
                <th className="px-3 py-2 text-left font-medium">Guardrail</th>
                <th className="px-3 py-2 text-left font-medium">Model</th>
                <th className="px-3 py-2 text-left font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {predictionRows.map((row) => {
                const needsReview = row.guardrail === "REVIEW" || row.guardrail === "WARN"
                return (
                  <tr
                    key={row.predictionId}
                    className="border-b border-border/20 last:border-0"
                  >
                    <td className="whitespace-nowrap px-3 py-1.5 font-mono text-[11px] text-muted-foreground">
                      {row.time}
                    </td>
                    <td className="whitespace-nowrap px-3 py-1.5 font-mono text-[11px]">
                      {row.predictionId}
                    </td>
                    <td className="max-w-[200px] truncate px-3 py-1.5" title={row.text}>
                      &ldquo;{row.text}&rdquo;
                    </td>
                    <td className="whitespace-nowrap px-3 py-1.5">{row.prediction}</td>
                    <td className="px-3 py-1.5 text-right font-mono tabular-nums">
                      {row.confidence.toFixed(2)}
                    </td>
                    <td className="px-3 py-1.5">
                      <StatusBadge status={row.guardrail} />
                    </td>
                    <td className="whitespace-nowrap px-3 py-1.5 font-mono text-[11px] text-muted-foreground">
                      {row.model}
                    </td>
                    <td className="px-3 py-1.5">
                      {needsReview ? (
                        <Link
                          href="/admin/review-queue"
                          className="text-[11px] font-medium text-foreground underline-offset-2 hover:underline"
                        >
                          Review
                        </Link>
                      ) : (
                        <Link
                          href="/admin/inference"
                          className="text-[11px] font-medium text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
                        >
                          View
                        </Link>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded border border-border/60 bg-card">
        <div className="flex items-center justify-between border-b border-border/50 px-3 py-2">
          <p className="text-[12px] font-medium">Review Queue Snapshot</p>
          <Link
            href="/admin/review-queue"
            className="text-[11px] text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
          >
            Open full queue
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[12px]">
            <thead>
              <tr className="border-b border-border/40 text-[10px] text-muted-foreground">
                <th className="px-3 py-2 text-left font-medium">Request ID</th>
                <th className="px-3 py-2 text-left font-medium">Reason</th>
                <th className="px-3 py-2 text-left font-medium">Priority</th>
                <th className="px-3 py-2 text-left font-medium">Created</th>
                <th className="px-3 py-2 text-left font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {reviewSnapshotRows.map((row) => (
                <tr key={row.requestId} className="border-b border-border/20 last:border-0">
                  <td className="whitespace-nowrap px-3 py-1.5 font-mono text-[11px]">
                    {row.requestId}
                  </td>
                  <td className="max-w-[240px] truncate px-3 py-1.5 text-muted-foreground">
                    {row.reason}
                  </td>
                  <td className="px-3 py-1.5">
                    <StatusBadge status={row.priority} />
                  </td>
                  <td className="whitespace-nowrap px-3 py-1.5 font-mono text-[11px] text-muted-foreground">
                    {row.created}
                  </td>
                  <td className="px-3 py-1.5">
                    <StatusBadge status={row.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <p className="text-[10px] text-muted-foreground">
        Refreshed {updatedAt} · error rate {monitoring.error_rate_pct}% · avg{" "}
        {monitoring.avg_latency_ms}ms
      </p>
    </div>
  )
}
