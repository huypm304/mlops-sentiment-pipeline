"use client"

import { useCallback, useEffect, useState } from "react"
import { Loader2, RefreshCw } from "lucide-react"
import { Bar, BarChart, CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"

import { ChartPanel } from "@/components/dashboard/chart-panel"
import { Button } from "@/components/ui/button"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import { EmptyState } from "@/components/ui/empty-state"
import { fetchRuntimeMetrics, type RuntimeMetrics } from "@/lib/api/runtime"
import { cn } from "@/lib/utils"

const latencyConfig = {
  latency: { label: "Latency (ms)", color: "var(--chart-1)" },
} satisfies ChartConfig

export function MonitoringView() {
  const [metrics, setMetrics] = useState<RuntimeMetrics | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    setError(null)
    try {
      const data = await fetchRuntimeMetrics()
      setMetrics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load runtime metrics")
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

  if (loading && !metrics) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading monitoring…
      </div>
    )
  }

  if (error && !metrics) {
    return <EmptyState title="Monitoring unavailable" description={error} />
  }

  if (!metrics) {
    return null
  }

  const healthy = metrics.endpoint_health === "healthy"
  const latencySeries = metrics.recent_latency_ms.map((ms, i) => ({
    n: i + 1,
    latency: ms,
  }))

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Operations
          </p>
          <h1 className="text-xl font-semibold tracking-tight">Monitoring</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Live inference API · refreshes every 15s
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

      <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <Stat
          label="API health"
          value={healthy ? "Healthy" : "Degraded"}
          ok={healthy}
        />
        <Stat label="Endpoint status" value={metrics.api_status} />
        <Stat
          label="Request volume"
          value={metrics.request_volume_total.toLocaleString()}
        />
        <Stat label="Avg latency" value={`${metrics.avg_latency_ms} ms`} />
        <Stat
          label="Error rate"
          value={`${metrics.error_rate_pct}%`}
          ok={metrics.error_rate_pct < 1 ? true : metrics.error_rate_pct > 5 ? false : undefined}
        />
      </dl>

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
            No requests yet — run a prediction from the customer app.
          </p>
        )}
      </ChartPanel>
    </div>
  )
}

function Stat({
  label,
  value,
  ok,
}: {
  label: string
  value: string
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
    </div>
  )
}
