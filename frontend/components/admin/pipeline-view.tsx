"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { AlertCircle, Loader2, PlayCircle, RefreshCw } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import {
  fetchPipelineConfig,
  fetchPipelineRuns,
  triggerPipeline,
} from "@/lib/api/pipeline"
import type { PipelineConfig, PipelineRun } from "@/types/pipeline"
import { cn } from "@/lib/utils"

const DATASET_OPTIONS = [
  { value: "datasets/raw/latest.jsonl", label: "datasets/raw/latest.jsonl" },
  { value: "datasets/raw/data_train.jsonl", label: "datasets/raw/data_train.jsonl" },
]

function statusVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  if (status === "SUCCEEDED") return "default"
  if (status === "FAILED") return "destructive"
  if (status === "RUNNING") return "secondary"
  return "outline"
}

function StageTimeline({ stages }: { stages: PipelineRun["stages"] }) {
  return (
    <ol className="mt-3 flex flex-wrap gap-2">
      {stages.map((stage) => (
        <li
          key={stage.name}
          className={cn(
            "rounded-md border px-2 py-1 text-[11px] font-medium",
            stage.status === "completed" && "border-chart-2/40 bg-chart-2/10 text-chart-2",
            stage.status === "running" && "border-primary/50 bg-primary/10 text-primary",
            stage.status === "failed" && "border-destructive/50 bg-destructive/10 text-destructive",
            stage.status === "pending" && "border-border/60 text-muted-foreground"
          )}
        >
          {stage.name}
        </li>
      ))}
    </ol>
  )
}

function RunCard({ run }: { run: PipelineRun }) {
  return (
    <Card className="border-white/[0.08] bg-white/[0.02]">
      <CardHeader className="pb-2">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle className="font-mono text-sm">{run.name}</CardTitle>
            <CardDescription className="mt-1">
              {run.dataset_key ?? "—"} · started {new Date(run.start_date).toLocaleString()}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {run.demo ? <Badge variant="outline">demo</Badge> : null}
            <Badge variant={statusVariant(run.status)}>{run.status}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {run.message ? (
          <p className="mb-2 text-xs text-muted-foreground">{run.message}</p>
        ) : null}
        <StageTimeline stages={run.stages} />
      </CardContent>
    </Card>
  )
}

export function PipelineView() {
  const [config, setConfig] = useState<PipelineConfig | null>(null)
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [datasetKey, setDatasetKey] = useState(DATASET_OPTIONS[0].value)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [triggering, setTriggering] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    setError(null)
    try {
      const [cfg, { runs: list }] = await Promise.all([
        fetchPipelineConfig(),
        fetchPipelineRuns(),
      ])
      setConfig(cfg)
      setRuns(list)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load pipeline")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(() => load(true), 12_000)
    return () => clearInterval(id)
  }, [load])

  const onTrigger = async () => {
    setTriggering(true)
    setError(null)
    try {
      const run = await triggerPipeline({ dataset_key: datasetKey })
      setRuns((prev) => [run, ...prev.filter((r) => r.execution_arn !== run.execution_arn)])
      await load(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start pipeline")
    } finally {
      setTriggering(false)
    }
  }

  if (loading && !config) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading pipeline…
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            MLOps
          </p>
          <h1 className="text-xl font-semibold tracking-tight">Retraining pipeline</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Step Functions: audit → clean → train → evaluate → register → deploy
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
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
          <Button size="sm" disabled={triggering} onClick={onTrigger} className="gap-2">
            {triggering ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : (
              <PlayCircle className="size-3.5" />
            )}
            Trigger Step Functions
          </Button>
        </div>
      </header>

      {config?.demo_mode ? (
        <div className="flex gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm">
          <AlertCircle className="mt-0.5 size-4 shrink-0 text-amber-500" />
          <div>
            <p className="font-medium text-amber-100">Local demo mode</p>
            <p className="mt-1 text-muted-foreground">{config.message}</p>
            <p className="mt-2 font-mono text-xs text-muted-foreground">
              RETRAIN_STATE_MACHINE_ARN=… ARTIFACTS_BUCKET=… AWS_REGION=ap-southeast-1
            </p>
          </div>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">{config?.message}</p>
      )}

      <Card className="border-white/[0.08] bg-white/[0.02]">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Start execution</CardTitle>
          <CardDescription>
            Invokes <code className="text-xs">POST /pipeline/trigger</code> → Step Functions{" "}
            <code className="text-xs">start_execution</code>
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted-foreground">Dataset S3 key</span>
            <select
              className="min-w-[280px] rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={datasetKey}
              onChange={(e) => setDatasetKey(e.target.value)}
            >
              {DATASET_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <Button disabled={triggering} onClick={onTrigger} className="gap-2">
            {triggering ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <PlayCircle className="size-4" />
            )}
            Trigger pipeline
          </Button>
          <Button variant="secondary" size="sm" asChild>
            <Link href="/admin/audit">Run audit first</Link>
          </Button>
        </CardContent>
      </Card>

      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}

      <section className="space-y-3">
        <h2 className="text-sm font-semibold">Recent runs</h2>
        {runs.length === 0 ? (
          <EmptyState
            title="No pipeline runs yet"
            description='Click "Trigger Step Functions" to start the retraining workflow.'
          />
        ) : (
          <div className="space-y-3">
            {runs.map((run) => (
              <RunCard key={run.execution_arn} run={run} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
