"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Loader2 } from "lucide-react"

import { EmptyState } from "@/components/ui/empty-state"
import { fetchModels, type ModelSummary } from "@/lib/api/metrics"
import { metricLabel } from "@/lib/constants/metrics"
import { cn } from "@/lib/utils"

// Model lifecycle states ordered by precedence
const STATUS_ORDER = [
  "production",
  "candidate",
  "approved",
  "previous_production",
  "rejected",
  "archived",
]

const STATUS_BADGE: Record<string, { label: string; className: string }> = {
  production: {
    label: "PRODUCTION",
    className: "bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/25",
  },
  candidate: {
    label: "CANDIDATE",
    className: "bg-blue-500/10 text-blue-400 ring-1 ring-blue-500/25",
  },
  approved: {
    label: "APPROVED",
    className: "bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/25",
  },
  previous_production: {
    label: "PREVIOUS",
    className: "bg-muted/60 text-muted-foreground ring-1 ring-border",
  },
  rejected: {
    label: "REJECTED",
    className: "bg-red-500/10 text-red-400 ring-1 ring-red-500/25",
  },
  archived: {
    label: "ARCHIVED",
    className: "bg-muted/40 text-muted-foreground/60 ring-1 ring-border/50",
  },
}

function StatusBadge({ status }: { status: string }) {
  const badge = STATUS_BADGE[status] ?? {
    label: status.toUpperCase(),
    className: "bg-muted/40 text-muted-foreground ring-1 ring-border/50",
  }
  return (
    <span className={cn("rounded px-1.5 py-0.5 text-[10px] font-semibold", badge.className)}>
      {badge.label}
    </span>
  )
}

function Metric({ value, highlight }: { value: number | null; highlight?: boolean }) {
  if (value === null || value === 0) {
    return <span className="text-muted-foreground/40">—</span>
  }
  return (
    <span className={cn("tabular-nums", highlight && "text-emerald-400 font-medium")}>
      {(value * 100).toFixed(1)}%
    </span>
  )
}

export function ModelsRegistry() {
  const [models, setModels] = useState<ModelSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchModels()
      .then((data) => {
        const sorted = [...data].sort((a, b) => {
          const ai = STATUS_ORDER.indexOf(a.status)
          const bi = STATUS_ORDER.indexOf(b.status)
          return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
        })
        setModels(sorted)
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load models"),
      )
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-10 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading registry…
      </div>
    )
  }

  if (error) {
    return <EmptyState title="Could not load models" description={error} />
  }

  if (models.length === 0) {
    return (
      <EmptyState
        title="No registered models"
        description="Ensure model/train_log.csv exists and the metrics API is running."
      />
    )
  }

  const prod = models.find((m) => m.status === "production")

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-[15px] font-semibold tracking-tight">Model Registry</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Registered model versions and their lifecycle status
        </p>
      </header>

      <div className="rounded-lg border border-border/60 bg-card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border/40 text-[11px] text-muted-foreground">
                <th className="px-4 py-2.5 text-left font-medium whitespace-nowrap">Version</th>
                <th className="px-4 py-2.5 text-left font-medium whitespace-nowrap">Status</th>
                <th className="px-4 py-2.5 text-left font-medium whitespace-nowrap">Encoder</th>
                <th className="px-4 py-2.5 text-right font-medium whitespace-nowrap">{metricLabel("tas_relaxed_f1")}</th>
                <th className="px-4 py-2.5 text-right font-medium whitespace-nowrap">{metricLabel("tas_strict_f1")}</th>
                <th className="px-4 py-2.5 text-right font-medium whitespace-nowrap">{metricLabel("span_f1")}</th>
                <th className="px-4 py-2.5 text-right font-medium whitespace-nowrap">{metricLabel("sent_matched_f1")}</th>
                <th className="px-4 py-2.5 text-right font-medium whitespace-nowrap">{metricLabel("global_f1")}</th>
                <th className="px-4 py-2.5 text-left font-medium whitespace-nowrap">Checkpoint</th>
                <th className="px-4 py-2.5 text-left font-medium whitespace-nowrap">Actions</th>
              </tr>
            </thead>
            <tbody>
              {models.map((m) => {
                const isProd = m.status === "production"
                const isCandidate = m.status === "candidate"
                const hasMetrics = m.tas_relaxed_f1 > 0

                return (
                  <tr
                    key={m.version}
                    className={cn(
                      "border-b border-border/20 last:border-0 transition-colors",
                      isProd && "bg-emerald-500/[0.03]",
                      isCandidate && "bg-blue-500/[0.02]",
                      "hover:bg-muted/20",
                    )}
                  >
                    <td className="px-4 py-2.5">
                      <span className="font-mono text-[13px] font-medium">{m.version}</span>
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap">
                      <StatusBadge status={m.status} />
                    </td>
                    <td className="px-4 py-2.5 font-mono text-[11px] text-muted-foreground whitespace-nowrap">
                      {m.encoder}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-[12px]">
                      {hasMetrics ? (
                        <>
                          <Metric value={m.tas_relaxed_f1} highlight={isProd} />
                          {prod && !isProd && hasMetrics && (
                            <DeltaBadge base={prod.tas_relaxed_f1} candidate={m.tas_relaxed_f1} />
                          )}
                        </>
                      ) : (
                        <span className="text-muted-foreground/40">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-[12px]">
                      {hasMetrics ? (
                        <>
                          <Metric value={m.tas_strict_f1} />
                          {prod && !isProd && hasMetrics && (
                            <DeltaBadge base={prod.tas_strict_f1} candidate={m.tas_strict_f1} />
                          )}
                        </>
                      ) : (
                        <span className="text-muted-foreground/40">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-[12px]">
                      {hasMetrics ? (
                        <>
                          <Metric value={m.span_f1} />
                          {prod && !isProd && hasMetrics && (
                            <DeltaBadge base={prod.span_f1} candidate={m.span_f1} />
                          )}
                        </>
                      ) : (
                        <span className="text-muted-foreground/40">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-[12px]">
                      {hasMetrics ? (
                        <>
                          <Metric value={m.sent_matched_f1} />
                          {prod && !isProd && hasMetrics && (
                            <DeltaBadge base={prod.sent_matched_f1} candidate={m.sent_matched_f1} />
                          )}
                        </>
                      ) : (
                        <span className="text-muted-foreground/40">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-[12px]">
                      {hasMetrics ? (
                        <>
                          <Metric value={m.global_f1} />
                          {prod && !isProd && hasMetrics && (
                            <DeltaBadge base={prod.global_f1} candidate={m.global_f1} />
                          )}
                        </>
                      ) : (
                        <span className="text-muted-foreground/40">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-[11px] text-muted-foreground whitespace-nowrap">
                      {m.checkpoint}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap">
                      {hasMetrics ? (
                        <Link
                          href={`/admin/models/${m.version}`}
                          className="text-[11px] text-primary/70 underline-offset-2 hover:text-primary hover:underline"
                        >
                          View
                        </Link>
                      ) : (
                        <span className="text-[11px] text-muted-foreground/40">
                          Not trained
                        </span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      <p className="text-[11px] text-muted-foreground">
        v2 promoted to PRODUCTION only if metric, cost, guardrail, and smoke-test gates all pass.
      </p>
    </div>
  )
}

function DeltaBadge({ base, candidate }: { base: number; candidate: number }) {
  const delta = candidate - base
  if (Math.abs(delta) < 0.001) return null
  const positive = delta > 0
  return (
    <span
      className={cn(
        "ml-1 text-[10px]",
        positive ? "text-emerald-400" : "text-red-400",
      )}
    >
      {positive ? "+" : ""}
      {(delta * 100).toFixed(1)}
    </span>
  )
}
