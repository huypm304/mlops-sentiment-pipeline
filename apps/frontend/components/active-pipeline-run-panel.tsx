"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import { Loader2, Square } from "lucide-react"

import { PipelineStageStepper, isActiveRunStatus } from "@/components/pipeline-stage-stepper"
import { Button } from "@/components/ui/button"
import { cancelPipelineRun, fetchPipelineRun } from "@/lib/api/pipeline"
import { appPath } from "@/lib/console/paths"
import type { PipelineRun } from "@/types/pipeline"

type Props = {
  run: PipelineRun
  onUpdate?: (run: PipelineRun) => void
  onCancelled?: () => void
  pollMs?: number
}

export function ActivePipelineRunPanel({ run: initialRun, onUpdate, onCancelled, pollMs = 3000 }: Props) {
  const [run, setRun] = useState(initialRun)
  const [cancelling, setCancelling] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runId = run.run_id ?? run.name

  const refresh = useCallback(async () => {
    if (!runId) return
    try {
      const detail = await fetchPipelineRun(runId)
      setRun(detail)
      onUpdate?.(detail)
    } catch {
      /* ignore transient poll errors */
    }
  }, [runId, onUpdate])

  useEffect(() => {
    setRun(initialRun)
  }, [initialRun])

  useEffect(() => {
    if (!isActiveRunStatus(run.status) && run.sfn_status !== "RUNNING") return
    refresh()
    const id = setInterval(refresh, pollMs)
    return () => clearInterval(id)
  }, [run.status, run.sfn_status, refresh, pollMs])

  const onCancel = async () => {
    if (!runId) return
    setCancelling(true)
    setError(null)
    try {
      await cancelPipelineRun(runId)
      await refresh()
      onCancelled?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không hủy được pipeline.")
    } finally {
      setCancelling(false)
    }
  }

  const steps = run.sfn_steps ?? run.stages ?? []
  const canCancel = isActiveRunStatus(run.status) || run.sfn_status === "RUNNING"

  return (
    <div className="space-y-3 rounded-lg border border-primary/30 bg-primary/5 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Pipeline đang chạy
          </p>
          <p className="font-mono text-sm">{runId}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Dataset: {run.dataset_id ?? "—"} · Base: {run.base_model_id ?? "absa-v2b"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {canCancel ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="gap-1.5 text-destructive hover:text-destructive"
              disabled={cancelling}
              onClick={onCancel}
            >
              {cancelling ? <Loader2 className="size-3.5 animate-spin" /> : <Square className="size-3.5" />}
              Hủy
            </Button>
          ) : null}
          <Link
            href={appPath(`/training-runs/${encodeURIComponent(runId)}`)}
            className="text-xs text-link hover:underline"
          >
            Chi tiết
          </Link>
        </div>
      </div>

      <PipelineStageStepper steps={steps} currentState={run.current_state} />

      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  )
}
