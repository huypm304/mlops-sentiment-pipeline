"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Loader2 } from "lucide-react"

import { ChartPanel } from "@/components/dashboard/chart-panel"
import { EmptyState } from "@/components/ui/empty-state"
import { fetchModels, type ModelSummary } from "@/lib/api/metrics"
import { cn } from "@/lib/utils"

export function ModelsRegistry() {
  const [models, setModels] = useState<ModelSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchModels()
      .then(setModels)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load models")
      )
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading registry…
      </div>
    )
  }

  if (error) {
    return (
      <EmptyState title="Could not load models" description={error} />
    )
  }

  if (models.length === 0) {
    return (
      <EmptyState
        title="No registered models"
        description="Ensure model/train_log.csv exists and the metrics API is running."
      />
    )
  }

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold tracking-tight">Model registry</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Trained checkpoint with evaluation from train_log.csv
        </p>
      </header>

      <ul className="space-y-3">
        {models.map((m) => (
          <li key={m.version}>
            <Link href={`/admin/models/${m.version}`} className="block">
              <ChartPanel
                title={
                  <>
                    <span className="font-mono">{m.version}</span>
                    <span
                      className={cn(
                        "ml-2 rounded px-1.5 py-0.5 text-[10px] font-medium capitalize",
                        m.status === "production"
                          ? "bg-chart-2/10 text-chart-2"
                          : "bg-white/5 text-muted-foreground"
                      )}
                    >
                      {m.status}
                    </span>
                  </>
                }
                description={`${m.encoder} · epoch ${m.epoch} · ${m.checkpoint}`}
                className="transition-colors hover:border-white/[0.12]"
              >
                <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                  <Metric label="Composite" value={m.composite} />
                  <Metric label="Sentiment F1" value={m.sent_f1} />
                  <Metric label="Span F1" value={m.span_f1} />
                  <Metric label="Global F1" value={m.glob_f1} />
                </dl>
              </ChartPanel>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt className="text-[10px] text-muted-foreground">{label}</dt>
      <dd className="font-mono font-medium tabular-nums">
        {(value * 100).toFixed(1)}%
      </dd>
    </div>
  )
}
