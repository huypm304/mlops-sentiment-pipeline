"use client"

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

import { ConsoleShell } from "@/components/layout/console-shell"
import { SectionHeader } from "@/components/console/section-header"
import { TableCard, ConsoleTable, ConsoleThead, ConsoleTh, ConsoleTr, ConsoleTd } from "@/components/console/table-card"
import { StatusBadge } from "@/components/console/status-badge"
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

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <SectionHeader title="Monitoring" description="Minimal operational metrics." />

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading monitoring
          </div>
        ) : (
          <>
            <div className="grid gap-3 md:grid-cols-3">
              <MetricCard label="API health" value={health?.endpoint_health ?? "unknown"} />
              <MetricCard label="Prediction count" value={String(analytics?.summary.predictions ?? 0)} />
              <MetricCard
                label="Low-confidence rate"
                value={`${Math.round((analytics?.summary.low_confidence_rate ?? 0) * 100)}%`}
              />
            </div>

            <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
              <TableCard
                title="Recent predictions"
                empty={!analytics || analytics.recent_predictions.length === 0}
                emptyLabel="No prediction records."
              >
                <ConsoleTable>
                  <ConsoleThead>
                    <tr>
                      <ConsoleTh>Time</ConsoleTh>
                      <ConsoleTh>Text</ConsoleTh>
                      <ConsoleTh align="right">Confidence</ConsoleTh>
                    </tr>
                  </ConsoleThead>
                  <tbody>
                    {analytics?.recent_predictions.slice(0, 12).map((row, idx) => (
                      <ConsoleTr key={`${row.time}-${idx}`}>
                        <ConsoleTd muted mono>{row.time}</ConsoleTd>
                        <ConsoleTd>{row.text}</ConsoleTd>
                        <ConsoleTd align="right" numeric>{(row.confidence * 100).toFixed(1)}%</ConsoleTd>
                      </ConsoleTr>
                    ))}
                  </tbody>
                </ConsoleTable>
              </TableCard>

              <div className="rounded-md border border-border bg-card">
                <div className="border-b border-border px-4 py-3">
                  <h2 className="text-sm font-semibold">Drift signal</h2>
                </div>
                <div className="space-y-2 px-4 py-4 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Status</span>
                    <StatusBadge value={monitoring?.drift.status ?? "unknown"} />
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Score</span>
                    <span className="tabular-nums">{(monitoring?.drift.drift_score ?? 0).toFixed(3)}</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Threshold</span>
                    <span className="tabular-nums">{(monitoring?.drift.threshold ?? 0).toFixed(3)}</span>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </section>
    </ConsoleShell>
  )
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-card px-4 py-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold capitalize">{value}</p>
    </div>
  )
}
