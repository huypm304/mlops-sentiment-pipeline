"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { AlertTriangle, Loader2, RefreshCw } from "lucide-react"
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, XAxis, YAxis } from "recharts"

import { ChartPanel } from "@/components/dashboard/chart-panel"
import { Button } from "@/components/ui/button"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import { EmptyState } from "@/components/ui/empty-state"
import { fetchMonitoring, type MonitoringPayload } from "@/lib/api/runtime"
import { cn } from "@/lib/utils"

const latencyConfig = {
  latency: { label: "Latency (ms)", color: "var(--chart-1)" },
} satisfies ChartConfig

const driftChartConfig = {
  baseline: { label: "Training baseline", color: "var(--chart-3)" },
  production: { label: "Production (live)", color: "var(--chart-1)" },
} satisfies ChartConfig

const ASPECT_NAMES = [
  "Fashion",
  "Electronics",
  "General",
  "Service",
  "Ship",
  "Price",
  "App",
]

function aspectComparisonChart(comparison: MonitoringPayload["drift"]["comparison"]) {
  return ASPECT_NAMES.map((name) => {
    const row = comparison.find((c) => c.name === name)
    return {
      name,
      baseline: row?.baseline ?? 0,
      production: row?.production ?? 0,
    }
  })
}

export function MonitoringView() {
  const [data, setData] = useState<MonitoringPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    setError(null)
    try {
      setData(await fetchMonitoring())
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load monitoring")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(() => load(true), 15_000)
    return () => clearInterval(id)
  }, [load])

  if (loading && !data) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading monitoring…
      </div>
    )
  }

  if (error && !data) {
    return <EmptyState title="Monitoring unavailable" description={error} />
  }

  if (!data) {
    return null
  }

  const metrics = data
  const drift = data.drift
  const healthy = metrics.endpoint_health === "healthy"
  const latencySeries = metrics.recent_latency_ms.map((ms, i) => ({
    n: i + 1,
    latency: ms,
  }))
  const aspectDriftData = aspectComparisonChart(drift.comparison)

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Operations
          </p>
          <h1 className="text-xl font-semibold tracking-tight">Monitoring</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            API health, latency, and drift vs training baseline
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={refreshing}
          onClick={() => load(true)}
          className="gap-2"
        >
          <RefreshCw className={cn("size-3.5", refreshing && "animate-spin")} />
          Refresh
        </Button>
      </header>

      {(drift.suggest_retrain || drift.status === "alert") && (
        <div className="flex flex-col gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-3">
            <AlertTriangle className="mt-0.5 size-5 shrink-0 text-amber-500" />
            <div>
              <p className="font-medium text-amber-100">Retrain recommended</p>
              <p className="mt-1 text-sm text-muted-foreground">{drift.message}</p>
              <ul className="mt-2 list-inside list-disc text-sm text-muted-foreground">
                {drift.signals.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2">
            <Button size="sm" variant="secondary" asChild>
              <Link href="/admin/audit">Run dataset audit</Link>
            </Button>
            <Button size="sm" asChild>
              <Link href="/admin/pipeline">Open pipeline</Link>
            </Button>
          </div>
        </div>
      )}

      <section className="space-y-3">
        <h2 className="text-sm font-semibold">Model & data drift</h2>
        <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Stat
            label="Drift score"
            value={
              drift.status === "insufficient_data"
                ? "—"
                : `${(drift.drift_score * 100).toFixed(1)}%`
            }
            ok={
              drift.status === "insufficient_data"
                ? undefined
                : drift.drift_score < drift.threshold
            }
          />
          <Stat label="Status" value={drift.status.replace("_", " ")} />
          <Stat
            label="Aspect drift"
            value={
              drift.status === "insufficient_data"
                ? "—"
                : `${(drift.aspect_drift * 100).toFixed(1)}%`
            }
          />
          <Stat
            label="Sentiment drift"
            value={
              drift.status === "insufficient_data"
                ? "—"
                : `${(drift.sentiment_drift * 100).toFixed(1)}%`
            }
          />
          <Stat
            label="Live samples"
            value={String(drift.production_sample_size)}
            sub={
              drift.status === "insufficient_data"
                ? `Need ≥5 predictions`
                : `baseline n=${drift.baseline.sample_size}`
            }
          />
        </dl>

        {drift.status === "insufficient_data" ? (
          <p className="text-sm text-muted-foreground">{drift.message}</p>
        ) : (
          <ChartPanel
            title="Aspect distribution: training vs production"
            description="Shift in opinion aspects may indicate data or concept drift"
          >
            <ChartContainer config={driftChartConfig} className="h-[220px] w-full">
              <BarChart data={aspectDriftData} margin={{ bottom: 48, left: 4, right: 4 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border/50" />
                <XAxis
                  dataKey="name"
                  interval={0}
                  tick={{ fontSize: 10 }}
                  angle={-35}
                  textAnchor="end"
                  height={52}
                />
                <YAxis tick={{ fontSize: 10 }} width={36} tickFormatter={(v) => `${(Number(v) * 100).toFixed(0)}%`} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Legend />
                <Bar dataKey="baseline" fill="var(--color-baseline)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="production" fill="var(--color-production)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ChartContainer>
          </ChartPanel>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold">API operations</h2>
        <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Stat label="API health" value={healthy ? "Healthy" : "Degraded"} ok={healthy} />
          <Stat label="Endpoint status" value={metrics.api_status} />
          <Stat label="Request volume" value={metrics.request_volume_total.toLocaleString()} />
          <Stat label="Avg latency" value={`${metrics.avg_latency_ms} ms`} />
          <Stat
            label="Error rate"
            value={`${metrics.error_rate_pct}%`}
            ok={metrics.error_rate_pct < 1 ? true : metrics.error_rate_pct > 5 ? false : undefined}
          />
        </dl>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartPanel title="Request volume" description="Total predictions since API start">
          <div className="flex h-[160px] flex-col items-center justify-center gap-1">
            <p className="font-mono text-4xl font-semibold tabular-nums">
              {metrics.request_volume_total}
            </p>
            <p className="text-xs text-muted-foreground">
              {metrics.error_count} errors · p95 {metrics.p95_latency_ms} ms
            </p>
          </div>
        </ChartPanel>

        <ChartPanel title="Error rate" description="Failed /predict requests">
          <ChartContainer
            config={{
              errors: { label: "Errors", color: "var(--chart-4)" },
              ok: { label: "OK", color: "var(--chart-2)" },
            }}
            className="h-[160px] w-full"
          >
            <BarChart
              data={[
                {
                  label: "Requests",
                  ok: Math.max(0, metrics.request_volume_total - metrics.error_count),
                  errors: metrics.error_count,
                },
              ]}
              layout="vertical"
            >
              <CartesianGrid horizontal={false} strokeDasharray="3 3" />
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="label" width={64} tick={{ fontSize: 10 }} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="ok" stackId="a" fill="var(--color-ok)" radius={[0, 4, 4, 0]} />
              <Bar dataKey="errors" stackId="a" fill="var(--color-errors)" radius={[4, 0, 0, 4]} />
            </BarChart>
          </ChartContainer>
        </ChartPanel>
      </div>

      <ChartPanel title="Latency" description="Recent inference response times (ms)">
        {latencySeries.length > 0 ? (
          <ChartContainer config={latencyConfig} className="h-[200px] w-full">
            <LineChart data={latencySeries}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis dataKey="n" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} width={40} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Line
                type="monotone"
                dataKey="latency"
                stroke="var(--color-latency)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ChartContainer>
        ) : (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No requests yet — run predictions from the customer app to populate drift metrics.
          </p>
        )}
      </ChartPanel>
    </div>
  )
}

function Stat({
  label,
  value,
  sub,
  ok,
}: {
  label: string
  value: string
  sub?: string
  ok?: boolean
}) {
  return (
    <div className="rounded-lg border border-white/[0.08] bg-white/[0.02] px-4 py-3">
      <dt className="text-[11px] text-muted-foreground">{label}</dt>
      <dd
        className={cn(
          "mt-1 text-lg font-semibold tabular-nums",
          ok === true && "text-chart-2",
          ok === false && "text-chart-4"
        )}
      >
        {value}
      </dd>
      {sub && <p className="mt-0.5 text-[10px] text-muted-foreground">{sub}</p>}
    </div>
  )
}
