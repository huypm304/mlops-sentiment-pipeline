"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { AlertCircle, CheckCircle2, Loader2, PlayCircle, RefreshCw } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { ActivePipelineRunPanel } from "@/components/active-pipeline-run-panel"
import { PipelineStageStepper } from "@/components/pipeline-stage-stepper"
import { TrainingConfigFields } from "@/components/training-config-fields"
import { fetchDataset, fetchDatasets } from "@/lib/api/datasets"
import {
  fetchDefaultTrainingConfig,
  fetchPipelineConfig,
  fetchPipelineRun,
  fetchPipelineRuns,
  triggerPipeline,
} from "@/lib/api/pipeline"
import type { DatasetListItem, DatasetManifest } from "@/types/dataset"
import {
  DEFAULT_TRAINING_CONFIG,
  type PipelineConfig,
  type PipelineRun,
  type TrainingConfig,
  type TrainingConfigField,
} from "@/types/pipeline"
import { cn } from "@/lib/utils"

function statusVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  if (status === "SUCCEEDED") return "default"
  if (status === "FAILED") return "destructive"
  if (status === "RUNNING") return "secondary"
  return "outline"
}

function RunCard({ run }: { run: PipelineRun }) {
  const steps = run.sfn_steps ?? []
  return (
    <Card className="border-white/[0.08] bg-white/[0.02]">
      <CardHeader className="pb-2">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle className="font-mono text-sm">{run.name}</CardTitle>
            <CardDescription className="mt-1">{run.dataset_key ?? run.run_id ?? "—"}</CardDescription>
          </div>
          <Badge variant={statusVariant(run.status)}>{run.status}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <PipelineStageStepper steps={steps} currentState={run.current_state} compact />
      </CardContent>
    </Card>
  )
}

export function PipelineView() {
  const [config, setConfig] = useState<PipelineConfig | null>(null)
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [registry, setRegistry] = useState<DatasetListItem[]>([])
  const [sessionDataset, setSessionDataset] = useState<DatasetManifest | null>(null)
  const [selectedDatasetId, setSelectedDatasetId] = useState("")
  const [trainingConfig, setTrainingConfig] = useState<TrainingConfig>(DEFAULT_TRAINING_CONFIG)
  const [baseModelId, setBaseModelId] = useState("absa-v2b")
  const [activeRun, setActiveRun] = useState<PipelineRun | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selectDataset = useCallback(async (datasetId: string) => {
    if (!datasetId) {
      setSessionDataset(null)
      setSelectedDatasetId("")
      return
    }
    setSelectedDatasetId(datasetId)
    const manifest = await fetchDataset(datasetId)
    setSessionDataset(manifest)
  }, [])

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    setError(null)
    try {
      const [cfg, listRes, defaults, datasets] = await Promise.all([
        fetchPipelineConfig().catch(() => null),
        fetchPipelineRuns().catch(() => ({ runs: [] as PipelineRun[] })),
        fetchDefaultTrainingConfig().catch(() => ({ training_config: {} as TrainingConfig })),
        fetchDatasets().catch(() => [] as DatasetListItem[]),
      ])
      const resolvedCfg: PipelineConfig = cfg ?? {
        configured: datasets.length > 0,
        demo_mode: false,
        state_machine_arn: null,
        artifacts_bucket: null,
        stages: ["Train", "Evaluate", "Compare", "Register", "Promote", "Deploy"],
        default_training_config: DEFAULT_TRAINING_CONFIG,
        message: "Pipeline config tạm thời không tải được.",
      }
      setConfig(resolvedCfg)
      setRuns(listRes.runs)
      setRegistry(datasets)
      setTrainingConfig({
        ...DEFAULT_TRAINING_CONFIG,
        ...resolvedCfg.default_training_config,
        ...defaults.training_config,
      })

      const running = listRes.runs.find((r) => r.status === "RUNNING")
      if (running) {
        try {
          const id = running.run_id ?? running.execution_arn
          setActiveRun(await fetchPipelineRun(id))
        } catch {
          setActiveRun(running)
        }
      } else {
        setActiveRun(null)
      }

      if (!selectedDatasetId && datasets.length > 0) {
        const preferred = datasets.find((d) => d.audit_passed) ?? datasets[0]
        await selectDataset(preferred.dataset_id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load pipeline")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [selectDataset, selectedDatasetId])

  useEffect(() => {
    load()
    const id = setInterval(() => load(true), 8000)
    return () => clearInterval(id)
  }, [load])

  useEffect(() => {
    if (!activeRun) return
    const id = activeRun.run_id ?? activeRun.execution_arn
    if (!id || !["RUNNING", "TRAINING", "TRAINING_IN_PROGRESS"].includes(activeRun.status.toUpperCase())) return
    const poll = async () => {
      try {
        const detail = await fetchPipelineRun(id)
        setActiveRun(detail)
        setRuns((prev) => prev.map((r) => ((r.run_id ?? r.execution_arn) === id ? detail : r)))
      } catch {
        /* ignore */
      }
    }
    poll()
    const timer = setInterval(poll, 5000)
    return () => clearInterval(timer)
  }, [activeRun?.run_id, activeRun?.execution_arn, activeRun?.status])

  const onTrigger = async () => {
    if (!sessionDataset) return
    setBusy(true)
    setError(null)
    try {
      const run = await triggerPipeline({
        dataset_id: sessionDataset.dataset_id,
        base_model_id: baseModelId,
        training_config: trainingConfig,
        requested_by: "admin-ui",
      })
      const runId = run.run_id ?? run.name
      let detail = run
      if (runId) {
        try {
          detail = await fetchPipelineRun(runId)
        } catch {
          detail = run
        }
      }
      setActiveRun(detail)
      setRuns((prev) => [detail, ...prev.filter((r) => r.execution_arn !== detail.execution_arn)])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start pipeline")
    } finally {
      setBusy(false)
    }
  }

  const updateConfig = (key: TrainingConfigField, value: string) => {
    const numeric = Number(value)
    setTrainingConfig((prev) => ({
      ...prev,
      [key]: Number.isFinite(numeric) ? numeric : value,
    }))
  }

  if (loading && !config) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading…
      </div>
    )
  }

  const canTrigger = Boolean(sessionDataset) && !config?.demo_mode && !busy

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">MLOps</p>
          <h1 className="text-xl font-semibold tracking-tight">Training Runs</h1>
          <p className="mt-1 text-sm text-muted-foreground">Chọn dataset → config → trigger. Data đã audit thủ công ở Datasets.</p>
        </div>
        <Button variant="outline" size="sm" disabled={refreshing} onClick={() => load(true)} className="gap-2">
          <RefreshCw className={cn("size-3.5", refreshing && "animate-spin")} />
          Refresh
        </Button>
      </header>

      {config?.demo_mode ? (
        <div className="flex gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm">
          <AlertCircle className="mt-0.5 size-4 shrink-0 text-amber-500" />
          <p className="text-muted-foreground">{config.message}</p>
        </div>
      ) : null}

      {activeRun && ["RUNNING", "TRAINING", "TRAINING_IN_PROGRESS", "TRAINING_COMPLETED", "EVALUATED", "COMPARED"].includes(activeRun.status.toUpperCase()) ? (
        <ActivePipelineRunPanel
          run={activeRun}
          onUpdate={(detail) => {
            setActiveRun(detail)
            setRuns((prev) =>
              prev.map((r) => ((r.run_id ?? r.execution_arn) === (detail.run_id ?? detail.execution_arn) ? detail : r)),
            )
          }}
          onCancelled={() => setActiveRun(null)}
        />
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="border-white/[0.08] bg-white/[0.02] lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm">Dataset</CardTitle>
            <CardDescription>
              Upload/audit tại{" "}
              <Link href="/admin/datasets" className="text-primary hover:underline">
                Datasets
              </Link>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {registry.length === 0 ? (
              <p className="text-xs text-muted-foreground">Chưa có dataset.</p>
            ) : (
              <select
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={selectedDatasetId}
                onChange={(e) => selectDataset(e.target.value).catch((err) => setError(String(err)))}
              >
                {registry.map((d) => (
                  <option key={d.dataset_id} value={d.dataset_id}>
                    {d.name} · {d.total_rows} rows{d.audit_passed ? " · audited" : ""}
                  </option>
                ))}
              </select>
            )}
            {sessionDataset ? (
              <div className="text-xs text-muted-foreground">
                <p className="font-mono text-foreground">{sessionDataset.dataset_id}</p>
                {sessionDataset.audit_passed ? (
                  <Badge className="mt-2 gap-1"><CheckCircle2 className="size-3" /> Audited</Badge>
                ) : null}
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card className="border-white/[0.08] bg-white/[0.02] lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm">Training config</CardTitle>
            <CardDescription>Architecture / evaluator locked in code version — chỉ chỉnh experiment params.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <label className="block text-xs">
              base_model_id
              <select
                className="mt-1 w-full max-w-xs rounded-md border border-input bg-background px-3 py-2 font-mono text-xs"
                value={baseModelId}
                onChange={(e) => setBaseModelId(e.target.value)}
              >
                <option value="absa-v2b">absa-v2b</option>
                <option value="absa-v1">absa-v1</option>
              </select>
            </label>
            <TrainingConfigFields
              className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
              value={trainingConfig}
              onChange={updateConfig}
            />
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button className="gap-2" disabled={!canTrigger} onClick={onTrigger}>
          {busy ? <Loader2 className="size-4 animate-spin" /> : <PlayCircle className="size-4" />}
          Start training
        </Button>
        {config?.demo_mode ? (
          <p className="text-xs text-muted-foreground">Cần cấu hình AWS Step Functions để chạy.</p>
        ) : null}
      </div>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <section className="space-y-3">
        <h2 className="text-sm font-semibold">Runs</h2>
        {runs.length === 0 ? (
          <EmptyState title="Chưa có run" description="Chọn dataset, config, rồi Start training." />
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
