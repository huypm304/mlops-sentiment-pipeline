"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

import { KpiStrip, PageFrame } from "@/components/console/page-frame"
import { StatusBadge } from "@/components/console/status-badge"
import {
  ConsoleTable,
  ConsoleTd,
  ConsoleTh,
  ConsoleThead,
  ConsoleTr,
  TableCard,
} from "@/components/console/table-card"
import { ConsoleShell } from "@/components/layout/console-shell"
import { appPath } from "@/lib/console/paths"
import { fetchAnalytics, type AnalyticsPayload } from "@/lib/api/analytics"
import { fetchHealth, fetchMonitoring } from "@/lib/api/runtime"

export default function MonitoringPage() {
  const [loading, setLoading] = useState(true)
  const [health, setHealth] = useState<Awaited<ReturnType<typeof fetchHealth>> | null>(null)
  const [monitoring, setMonitoring] = useState<Awaited<ReturnType<typeof fetchMonitoring>> | null>(null)
  const [analytics, setAnalytics] = useState<AnalyticsPayload | null>(null)

  useEffect(() => {
    Promise.all([
      fetchHealth().then(setHealth).catch(() => setHealth(null)),
      fetchMonitoring().then(setMonitoring).catch(() => setMonitoring(null)),
      fetchAnalytics(24).then(setAnalytics).catch(() => setAnalytics(null)),
    ]).finally(() => setLoading(false))
  }, [])

  const drift = monitoring?.drift
  const summary = analytics?.summary
  const healthy = health?.endpoint_health === "healthy"

  return (
    <ConsoleShell>
      <PageFrame
        title="Monitoring"
        description="Track API reliability, prediction quality, and review signals for the active production model."
        breadcrumbs={[
          { label: "ABSA Studio", href: "/" },
          { label: "Observe" },
          { label: "Monitoring" },
        ]}
      >
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading signals…
          </div>
        ) : (
          <>
            {drift?.suggest_retrain ? (
              <div className="flex flex-col gap-2 rounded-md border border-border bg-muted/25 px-3 py-2.5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-[13px] font-medium">Model behavior changed</p>
                  <p className="text-[12px] text-muted-foreground">
                    Production traffic differs from the training baseline. Review recent samples
                    before starting a new training run.
                  </p>
                </div>
                <div className="flex gap-2">
                  <Link
                    href="/monitoring#predictions"
                    className="rounded border border-border bg-background px-2.5 py-1.5 text-[11px] font-medium hover:bg-muted/40"
                  >
                    View samples
                  </Link>
                  <Link
                    href="/training-runs"
                    className="rounded border border-primary/30 bg-primary/10 px-2.5 py-1.5 text-[11px] font-medium text-primary hover:bg-primary/15"
                  >
                    Create retrain request
                  </Link>
                </div>
              </div>
            ) : null}

            <KpiStrip
              items={[
                {
                  label: "API health",
                  value: healthy ? "Healthy" : "Degraded",
                  tone: healthy ? "ok" : "warn",
                },
                {
                  label: "Predictions",
                  value: String(summary?.predictions ?? 0),
                  hint: "last 24h",
                },
                {
                  label: "Low-confidence",
                  value: `${(summary?.low_confidence_rate ?? 0).toFixed(1)}%`,
                  hint: `threshold ${summary?.low_confidence_threshold_pct ?? 32}%`,
                  tone: (summary?.low_confidence_rate ?? 0) > (summary?.low_confidence_threshold_pct ?? 32) ? "warn" : "ok",
                },
                {
                  label: "Review queue",
                  value: `${summary?.review_queue_pending ?? 0} pending`,
                  hint: `${summary?.review_queue_urgent ?? 0} urgent`,
                },
                {
                  label: "p95 latency",
                  value: `${health?.p95_latency_ms ?? monitoring?.p95_latency_ms ?? 0}ms`,
                  hint: "target < 1500ms",
                  tone: (health?.p95_latency_ms ?? 0) < 1500 ? "ok" : "warn",
                },
              ]}
            />

            <div className="rounded-md border border-border bg-card">
              <div className="border-b border-border px-3 py-2">
                <p className="text-[12px] font-semibold">Drift signals</p>
              </div>
              <dl className="grid sm:grid-cols-2 lg:grid-cols-4">
                {[
                  {
                    label: "Aspect distribution",
                    value:
                      drift && drift.aspect_drift >= (drift.threshold ?? 0.18) ? "Warning" : "Normal",
                  },
                  {
                    label: "Sentiment distribution",
                    value:
                      drift && drift.sentiment_drift >= (drift.threshold ?? 0.18)
                        ? "Warning"
                        : "Normal",
                  },
                  { label: "Text length", value: "Normal" },
                  {
                    label: "Overall",
                    value: drift?.suggest_retrain ? "Review recommended" : "Stable",
                  },
                ].map((row) => (
                  <div key={row.label} className="border-b border-r border-border/50 px-3 py-2.5 last:border-r-0">
                    <dt className="text-[10px] text-muted-foreground">{row.label}</dt>
                    <dd className="mt-0.5 text-[12px] font-medium">{row.value}</dd>
                  </div>
                ))}
              </dl>
            </div>

            <TableCard
              title="Recent predictions"
              empty={!analytics || analytics.recent_predictions.length === 0}
              emptyLabel="No prediction records. Run inference to populate the log."
            >
              <div id="predictions">
                <ConsoleTable>
                  <ConsoleThead>
                    <tr>
                      <ConsoleTh>Time</ConsoleTh>
                      <ConsoleTh>Text</ConsoleTh>
                      <ConsoleTh>Prediction</ConsoleTh>
                      <ConsoleTh align="right">Confidence</ConsoleTh>
                      <ConsoleTh>Guardrail</ConsoleTh>
                      <ConsoleTh>Model</ConsoleTh>
                      <ConsoleTh>Action</ConsoleTh>
                    </tr>
                  </ConsoleThead>
                  <tbody>
                    {analytics?.recent_predictions.slice(0, 12).map((row, idx) => {
                      const guardrail = row.guardrail || "PASS"
                      return (
                      <ConsoleTr key={`${row.time}-${idx}`}>
                        <ConsoleTd muted mono>
                          {row.time || "—"}
                        </ConsoleTd>
                        <ConsoleTd className="max-w-[200px] truncate" title={row.text}>
                          {row.text || "—"}
                        </ConsoleTd>
                        <ConsoleTd muted>
                          {row.sentiment || "—"}
                          {(row.aspects ?? []).length
                            ? ` · ${(row.aspects ?? []).slice(0, 2).join(", ")}`
                            : ""}
                        </ConsoleTd>
                        <ConsoleTd align="right" numeric>
                          {((Number(row.confidence) || 0) * 100).toFixed(0)}%
                        </ConsoleTd>
                        <ConsoleTd>
                          <StatusBadge value={guardrail} />
                        </ConsoleTd>
                        <ConsoleTd mono muted>
                          {row.model_version}
                        </ConsoleTd>
                        <ConsoleTd>
                          {guardrail === "PASS" ? (
                            <span className="text-muted-foreground/50">—</span>
                          ) : (
                            <Link href={appPath("/inference")} className="text-[11px] text-primary hover:underline">
                              Review
                            </Link>
                          )}
                        </ConsoleTd>
                      </ConsoleTr>
                    )})}
                  </tbody>
                </ConsoleTable>
              </div>
            </TableCard>
          </>
        )}
      </PageFrame>
    </ConsoleShell>
  )
}
