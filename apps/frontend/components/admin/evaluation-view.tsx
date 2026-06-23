"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Loader2 } from "lucide-react"

import { EvaluationReport } from "@/components/evaluation/evaluation-report"
import { EmptyState } from "@/components/ui/empty-state"
import {
  fetchModelEvaluation,
  fetchTrainingHistory,
  type TrainingHistoryPoint,
} from "@/lib/api/metrics"
import type { ModelEvaluation } from "@/types/evaluation"

const PRODUCTION_VERSION = "best"

export function EvaluationView() {
  const [evaluation, setEvaluation] = useState<ModelEvaluation | null>(null)
  const [history, setHistory] = useState<TrainingHistoryPoint[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetchModelEvaluation(PRODUCTION_VERSION),
      fetchTrainingHistory(),
    ])
      .then(([ev, hist]) => {
        setEvaluation(ev)
        setHistory(hist)
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load evaluation data")
      )
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading evaluation report…
      </div>
    )
  }

  if (error || !evaluation) {
    return (
      <EmptyState
        title="Could not load evaluation"
        description={
          error ??
          "Ensure the model is registered in DynamoDB with S3 artifacts (train_log.csv) and the metrics API is running."
        }
      />
    )
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          Model evaluation
        </p>
        <h1 className="text-xl font-semibold tracking-tight">Evaluation report</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Production model{" "}
          <Link
            href={`/admin/models/${evaluation.version}`}
            className="font-mono text-primary hover:underline"
          >
            {evaluation.version}
          </Link>
          {" · "}
          epoch {evaluation.epoch} · {evaluation.training.encoder}
        </p>
      </header>

      <EvaluationReport evaluation={evaluation} history={history} />
    </div>
  )
}
