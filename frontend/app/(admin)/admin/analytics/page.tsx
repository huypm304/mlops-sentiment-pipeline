"use client"

import { useCallback, useEffect, useState } from "react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Tooltip as RechartTooltip,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts"
import { Loader2, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { fetchAnalytics, type AnalyticsPayload } from "@/lib/api/analytics"
import { cn } from "@/lib/utils"

const GUARDRAIL_STYLES = {
  PASS: "bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/25",
  WARN: "bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/25",
  REVIEW: "bg-blue-500/10 text-blue-400 ring-1 ring-blue-500/25",
  REJECT: "bg-red-500/10 text-red-400 ring-1 ring-red-500/25",
}

const SENTIMENT_STYLES: Record<string, string> = {
  positive: "text-emerald-400",
  negative: "text-red-400",
  mixed: "text-amber-400",
  neutral: "text-muted-foreground",
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: { name: string; value: number; color: string }[]
  label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded border border-border/60 bg-popover px-2.5 py-2 text-[11px] shadow-lg">
      {label && <p className="mb-1 font-medium">{label}</p>}
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}:{" "}
          {typeof p.value === "number" && p.value < 1
            ? `${(p.value * 100).toFixed(1)}%`
            : p.value}
        </p>
      ))}
    </div>
  )
}

function StatCard({
  label,
  value,
  sub,
  status,
}: {
  label: string
  value: string
  sub?: string
  status?: "ok" | "warn" | "muted"
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-card px-4 py-3">
      <p className="text-[11px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p
        className={cn(
          "mt-1 text-xl font-semibold tabular-nums",
          status === "ok" && "text-emerald-400",
          status === "warn" && "text-amber-400",
          status === "muted" && "text-muted-foreground",
        )}
      >
        {value}
      </p>
      {sub && <p className="mt-0.5 text-[10px] text-muted-foreground">{sub}</p>}
    </div>
  )
}

function Panel({
  title,
  children,
  empty,
}: {
  title: string
  children: React.ReactNode
  empty?: boolean
}) {
  return (
    <section className="flex flex-col rounded-lg border border-border/60 bg-card">
      <div className="border-b border-border/40 px-4 py-2">
        <p className="text-[12px] font-medium">{title}</p>
      </div>
      <div className="flex-1 p-4">
        {empty ? (
          <p className="py-8 text-center text-sm text-muted-foreground">No data yet</p>
        ) : (
          children
        )}
      </div>
    </section>
  )
}

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState("24")
  const [model, setModel] = useState("")
  const [data, setData] = useState<AnalyticsPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const load = useCallback(
    async (silent = false) => {
      if (!silent) setLoading(true)
      else setRefreshing(true)
      setError(null)
      try {
        const payload = await fetchAnalytics(Number(timeRange), model || undefined)
        setData(payload)
        if (!model && payload.models.length > 0) {
          setModel(payload.models[0])
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analytics")
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [timeRange, model],
  )

  useEffect(() => {
    load()
  }, [load])

  if (loading && !data) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading analytics…
      </div>
    )
  }

  if (error && !data) {
    return <EmptyState title="Analytics unavailable" description={error} />
  }

  if (!data) return null

  const { summary } = data

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-[15px] font-semibold tracking-tight">Analytics</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Prediction distribution from inference log
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="h-8 rounded-md border border-border/70 bg-background px-2 text-xs"
          >
            <option value="1">Last 1h</option>
            <option value="24">Last 24h</option>
            <option value="168">Last 7d</option>
            <option value="720">Last 30d</option>
          </select>

          {data.models.length > 0 && (
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="h-8 rounded-md border border-border/70 bg-background px-2 text-xs"
            >
              {data.models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          )}

          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-1.5 text-xs"
            disabled={refreshing}
            onClick={() => load(true)}
          >
            <RefreshCw className={cn("size-3", refreshing && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard
          label="Predictions"
          value={summary.predictions.toLocaleString()}
          sub={`Last ${timeRange}h · ${model || "all models"}`}
        />
        <StatCard
          label="Low-confidence rate"
          value={`${summary.low_confidence_rate}%`}
          sub="Below 32% global confidence"
          status={summary.low_confidence_rate > 20 ? "warn" : undefined}
        />
        <StatCard
          label="No-opinion rate"
          value={`${summary.no_opinion_rate}%`}
          sub="Empty aspect output"
          status={summary.no_opinion_rate > 10 ? "warn" : undefined}
        />
        <StatCard
          label="Review queue"
          value={String(summary.review_queue)}
          sub="Flagged predictions"
          status={summary.review_queue > 0 ? "warn" : "ok"}
        />
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <Panel title="Sentiment trend" empty={data.sentiment_trend.length === 0}>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={data.sentiment_trend} margin={{ left: -10, right: 8 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" className="stroke-border/30" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={32} />
              <RechartTooltip content={<ChartTooltip />} />
              <Line type="monotone" dataKey="positive" name="Positive" stroke="oklch(0.72 0.12 165)" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="neutral" name="Neutral" stroke="oklch(0.58 0.02 260)" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="negative" name="Negative" stroke="oklch(0.65 0.2 25)" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Aspect distribution" empty={data.aspect_distribution.length === 0}>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={data.aspect_distribution} layout="vertical" margin={{ left: 4, right: 16 }}>
              <CartesianGrid horizontal={false} strokeDasharray="3 3" className="stroke-border/30" />
              <XAxis type="number" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="aspect" width={72} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
              <RechartTooltip content={<ChartTooltip />} />
              <Bar dataKey="count" name="Count" radius={[0, 3, 3, 0]} fill="oklch(0.72 0.14 220)" />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <Panel title="Confidence distribution" empty={summary.predictions === 0}>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={data.confidence_histogram} margin={{ left: -10, right: 8 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" className="stroke-border/30" />
              <XAxis dataKey="bin" tick={{ fontSize: 9 }} tickLine={false} axisLine={false} angle={-30} textAnchor="end" height={40} />
              <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={32} />
              <RechartTooltip content={<ChartTooltip />} />
              <Bar dataKey="count" name="Predictions" radius={[3, 3, 0, 0]}>
                {data.confidence_histogram.map((_, i) => {
                  const color =
                    i < 4 ? "oklch(0.65 0.2 25)" : i < 6 ? "oklch(0.78 0.14 85)" : "oklch(0.72 0.12 165)"
                  return <Cell key={i} fill={color} fillOpacity={0.75} />
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Drift signal" empty={data.drift.status === "insufficient_data"}>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={data.drift_trend} margin={{ left: -10, right: 8 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" className="stroke-border/30" />
              <XAxis dataKey="day" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={40} tickFormatter={(v) => `${(Number(v) * 100).toFixed(0)}%`} />
              <RechartTooltip content={<ChartTooltip />} />
              <Line
                type="monotone"
                dataKey={() => data.drift.threshold}
                name="Threshold"
                stroke="oklch(0.65 0.2 25 / 0.35)"
                strokeWidth={1}
                strokeDasharray="4 4"
                dot={false}
              />
              <Line type="monotone" dataKey="score" name="Drift score" stroke="oklch(0.72 0.14 220)" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
          <p className="mt-1 text-[10px] text-muted-foreground">
            Threshold: {(data.drift.threshold * 100).toFixed(0)}% · Status: {data.drift.status}
          </p>
        </Panel>
      </div>

      <div className="rounded-lg border border-border/60 bg-card">
        <div className="flex items-center justify-between border-b border-border/40 px-4 py-2.5">
          <p className="text-[12px] font-medium">Recent Predictions</p>
          <span className="text-[10px] text-muted-foreground">{model || "all models"}</span>
        </div>
        {data.recent_predictions.length === 0 ? (
          <p className="px-4 py-8 text-center text-sm text-muted-foreground">
            Run inference to populate the log
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/30 text-[11px] text-muted-foreground">
                  <th className="px-4 py-2 text-left font-medium">Time</th>
                  <th className="px-4 py-2 text-left font-medium">Text</th>
                  <th className="px-4 py-2 text-left font-medium">Aspects</th>
                  <th className="px-4 py-2 text-left font-medium">Sentiment</th>
                  <th className="px-4 py-2 text-left font-medium">Confidence</th>
                  <th className="px-4 py-2 text-left font-medium">Guardrail</th>
                  <th className="px-4 py-2 text-left font-medium">Model</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_predictions.map((row, i) => (
                  <tr key={i} className="border-b border-border/20 last:border-0 hover:bg-muted/20">
                    <td className="px-4 py-2 font-mono text-[11px] text-muted-foreground">{row.time}</td>
                    <td className="max-w-[240px] truncate px-4 py-2 text-[12px]">{row.text}</td>
                    <td className="px-4 py-2">
                      <div className="flex flex-wrap gap-1">
                        {row.aspects.length > 0 ? (
                          row.aspects.map((a) => (
                            <span key={a} className="rounded bg-muted/60 px-1.5 py-0.5 text-[10px] text-muted-foreground">
                              {a}
                            </span>
                          ))
                        ) : (
                          <span className="text-[11px] text-muted-foreground/50">—</span>
                        )}
                      </div>
                    </td>
                    <td className={cn("px-4 py-2 text-[12px] capitalize", SENTIMENT_STYLES[row.sentiment])}>
                      {row.sentiment}
                    </td>
                    <td className="px-4 py-2 font-mono text-[12px] tabular-nums">
                      {(row.confidence * 100).toFixed(0)}%
                    </td>
                    <td className="px-4 py-2">
                      <span className={cn("rounded px-1.5 py-0.5 text-[10px] font-medium", GUARDRAIL_STYLES[row.guardrail])}>
                        {row.guardrail}
                      </span>
                    </td>
                    <td className="px-4 py-2 font-mono text-[11px] text-muted-foreground">{row.model_version}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
