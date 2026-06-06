"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { ArrowRight, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { fetchAnalytics } from "@/lib/api/analytics"
import { fetchHealth, fetchMonitoring } from "@/lib/api/runtime"
import { cn } from "@/lib/utils"

function QuickStat({
  label,
  value,
  meta,
}: {
  label: string
  value: string
  meta?: string
}) {
  return (
    <div className="rounded-md border border-border/60 bg-card px-3 py-2.5">
      <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 font-mono text-[15px] font-semibold tabular-nums">{value}</p>
      {meta ? <p className="mt-0.5 text-[10px] text-muted-foreground">{meta}</p> : null}
    </div>
  )
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [health, setHealth] = useState<Awaited<ReturnType<typeof fetchHealth>> | null>(null)
  const [analytics, setAnalytics] = useState<Awaited<ReturnType<typeof fetchAnalytics>> | null>(null)
  const [driftStatus, setDriftStatus] = useState<string>("—")

  useEffect(() => {
    Promise.all([
      fetchHealth().then(setHealth),
      fetchAnalytics(24).then(setAnalytics).catch(() => null),
      fetchMonitoring()
        .then((m) => setDriftStatus(m.drift.status.replace("_", " ")))
        .catch(() => null),
    ]).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading dashboard…
      </div>
    )
  }

  const healthy = health?.endpoint_health === "healthy"
  const summary = analytics?.summary

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-border/50 pb-3">
        <div>
          <h1 className="text-[15px] font-semibold tracking-tight">Dashboard</h1>
          <p className="mt-0.5 text-[13px] text-muted-foreground">
            Production control plane for Vietnamese ABSA inference and retraining.
          </p>
        </div>
        <Button size="sm" className="h-8 text-xs" asChild>
          <Link href="/admin/monitoring">
            Operations console
            <ArrowRight className="ml-1 size-3" />
          </Link>
        </Button>
      </header>

      <section className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <QuickStat
          label="API health"
          value={healthy ? "Healthy" : "Degraded"}
          meta={health?.api_status}
        />
        <QuickStat
          label="Predictions (24h)"
          value={String(summary?.predictions ?? 0)}
        />
        <QuickStat
          label="Review queue"
          value={`${summary?.review_queue_pending ?? 0} pending`}
          meta={`${summary?.review_queue_urgent ?? 0} urgent`}
        />
        <QuickStat label="Drift status" value={driftStatus} />
      </section>

      <section className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { href: "/admin/datasets", label: "Upload dataset", sub: "Train / dev / test JSONL" },
          { href: "/admin/inference", label: "Inference", sub: "Manual model test" },
          { href: "/admin/review-queue", label: "Review queue", sub: "Flagged predictions" },
          { href: "/admin/pipeline", label: "Training runs", sub: "Retrain pipeline" },
        ].map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "rounded-md border border-border/60 bg-card px-3 py-3 transition-colors hover:bg-muted/30",
            )}
          >
            <p className="text-[13px] font-medium">{item.label}</p>
            <p className="mt-0.5 text-[11px] text-muted-foreground">{item.sub}</p>
          </Link>
        ))}
      </section>
    </div>
  )
}
