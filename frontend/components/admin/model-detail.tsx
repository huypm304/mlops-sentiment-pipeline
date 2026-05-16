"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { ArrowLeft, BarChart3, Loader2 } from "lucide-react"

import { ChartPanel } from "@/components/dashboard/chart-panel"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { fetchModelEvaluation } from "@/lib/api/metrics"
import type { ModelEvaluation } from "@/types/evaluation"
import { cn } from "@/lib/utils"

type ModelDetailProps = {
  version: string
}

export function ModelDetail({ version }: ModelDetailProps) {
  const [evaluation, setEvaluation] = useState<ModelEvaluation | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchModelEvaluation(version)
      .then((data) => {
        if (!cancelled) setEvaluation(data)
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load model")
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [version])

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading model…
      </div>
    )
  }

  if (error || !evaluation) {
    return (
      <div className="space-y-4">
        <BackLink />
        <EmptyState title="Model not found" description={error ?? undefined} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <BackLink />
          <h1 className="font-mono text-2xl font-semibold tracking-tight">
            {evaluation.version}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Model registry entry · {evaluation.training.encoder}
          </p>
        </div>
        <span
          className={cn(
            "w-fit rounded-md border px-2.5 py-1 text-xs font-medium capitalize",
            evaluation.status === "production"
              ? "border-chart-2/30 bg-chart-2/10 text-chart-2"
              : "border-white/10 bg-white/5 text-muted-foreground"
          )}
        >
          {evaluation.status}
        </span>
      </div>

      <ChartPanel title="Artifact" description="Deployed checkpoint">
        <dl className="grid gap-4 sm:grid-cols-2">
          <Field label="Checkpoint" value={evaluation.training.checkpoint} mono />
          <Field label="Encoder" value={evaluation.training.encoder} />
          <Field label="Training epochs" value={String(evaluation.training.epochs)} />
          <Field label="Batch size" value={String(evaluation.training.batchSize)} />
          <Field
            label="Best epoch"
            value={evaluation.epoch ? String(evaluation.epoch) : "—"}
          />
          <Field label="Dataset" value={evaluation.dataset.version} />
        </dl>
      </ChartPanel>

      {evaluation.scores ? (
        <ChartPanel title="Validation summary" description="Best checkpoint on held-out set">
          <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Metric label="Composite" value={evaluation.scores.composite} />
            <Metric label="Span F1" value={evaluation.scores.span_f1} />
            <Metric label="Sentiment F1" value={evaluation.scores.sent_f1} />
            <Metric label="Global F1" value={evaluation.scores.glob_f1} />
          </dl>
          <div className="mt-4 border-t border-white/[0.06] pt-4">
            <Button size="sm" className="gap-2" asChild>
              <Link href="/admin/evaluation">
                <BarChart3 className="size-4" />
                Full evaluation report
              </Link>
            </Button>
            <p className="mt-2 text-xs text-muted-foreground">
              Training curves, confusion matrix, and per-aspect metrics live under Evaluation.
            </p>
          </div>
        </ChartPanel>
      ) : null}
    </div>
  )
}

function BackLink() {
  return (
    <Button variant="ghost" size="sm" className="-ml-2 mb-2 h-8 gap-1 text-xs" asChild>
      <Link href="/admin/models">
        <ArrowLeft className="size-3.5" />
        Registry
      </Link>
    </Button>
  )
}

function Field({
  label,
  value,
  mono,
}: {
  label: string
  value: string
  mono?: boolean
}) {
  return (
    <div>
      <dt className="text-[10px] text-muted-foreground">{label}</dt>
      <dd className={cn("mt-0.5 text-sm font-medium", mono && "font-mono")}>{value}</dd>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt className="text-[10px] text-muted-foreground">{label}</dt>
      <dd className="font-mono text-lg font-semibold tabular-nums">
        {(value * 100).toFixed(1)}%
      </dd>
    </div>
  )
}
