"use client"

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

import { EmptyState } from "@/components/ui/empty-state"
import { fetchPlatformSettings, type PlatformSettings } from "@/lib/api/analytics"
import { fetchMonitoring } from "@/lib/api/runtime"

function formatUptime(seconds: number) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

export default function CostPage() {
  const [platform, setPlatform] = useState<PlatformSettings | null>(null)
  const [runtime, setRuntime] = useState<Awaited<ReturnType<typeof fetchMonitoring>> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([fetchPlatformSettings(), fetchMonitoring()])
      .then(([p, r]) => {
        setPlatform(p)
        setRuntime(r)
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load usage data"),
      )
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading usage…
      </div>
    )
  }

  if (error || !platform || !runtime) {
    return <EmptyState title="Usage data unavailable" description={error ?? undefined} />
  }

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-[15px] font-semibold tracking-tight">Cost &amp; Usage</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Local runtime usage from inference API
        </p>
      </header>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-border/60 bg-card px-4 py-3">
          <p className="text-[11px] text-muted-foreground">API requests</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">
            {runtime.request_volume_total.toLocaleString()}
          </p>
          <p className="mt-0.5 text-[10px] text-muted-foreground">
            {runtime.error_count} errors
          </p>
        </div>
        <div className="rounded-lg border border-border/60 bg-card px-4 py-3">
          <p className="text-[11px] text-muted-foreground">Avg latency</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">
            {runtime.avg_latency_ms} ms
          </p>
          <p className="mt-0.5 text-[10px] text-muted-foreground">
            p95 {runtime.p95_latency_ms} ms
          </p>
        </div>
        <div className="rounded-lg border border-border/60 bg-card px-4 py-3">
          <p className="text-[11px] text-muted-foreground">Endpoint status</p>
          <p className="mt-1 text-base font-semibold capitalize">
            {platform.endpoint_status}
          </p>
          <p className="mt-0.5 text-[10px] text-muted-foreground">
            Uptime {formatUptime(platform.uptime_seconds)}
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-border/60 bg-card">
        <div className="border-b border-border/60 px-4 py-2.5">
          <p className="text-[12px] font-medium uppercase tracking-wider text-muted-foreground">
            Runtime breakdown
          </p>
        </div>
        <table className="w-full text-sm">
          <tbody>
            <UsageRow label="Environment" value={platform.environment} />
            <UsageRow label="Production model" value={platform.production_model} />
            <UsageRow label="Model directory" value={platform.model_dir} />
            <UsageRow label="Drift predictions logged" value={String(runtime.drift.production_sample_size)} />
            <UsageRow label="Error rate" value={`${runtime.error_rate_pct}%`} />
            <UsageRow label="Pipeline demo mode" value={platform.pipeline_demo_mode ? "enabled" : "disabled"} />
            <UsageRow label="Artifacts bucket" value={platform.artifacts_bucket ?? "not configured"} />
          </tbody>
        </table>
      </div>

      <p className="text-[11px] text-muted-foreground">
        AWS cost estimates are available after deploying runtime infrastructure via Terraform.
      </p>
    </div>
  )
}

function UsageRow({ label, value }: { label: string; value: string }) {
  return (
    <tr className="border-b border-border/30 last:border-0">
      <td className="px-4 py-2.5 text-[13px]">{label}</td>
      <td className="px-4 py-2.5 text-right font-mono text-[12px] text-muted-foreground">{value}</td>
    </tr>
  )
}
