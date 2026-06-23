"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import { Loader2, PlayCircle, Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { fetchDatasets } from "@/lib/api/datasets"
import { fetchDefaultTrainingConfig, fetchPipelineConfig, triggerPipeline } from "@/lib/api/pipeline"
import { appPath } from "@/lib/console/paths"
import type { DatasetListItem } from "@/types/dataset"
import {
  TRAINING_CONFIG_FIELDS,
  type PipelineConfig,
  type PipelineRun,
  type TrainingConfig,
  type TrainingConfigField,
} from "@/types/pipeline"

type Props = {
  onStarted?: (run: PipelineRun) => void
}

const BASE_MODEL_OPTIONS = ["absa-v2b", "absa-v1"] as const

export function NewTrainingRunSheet({ onStarted }: Props) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [config, setConfig] = useState<PipelineConfig | null>(null)
  const [datasets, setDatasets] = useState<DatasetListItem[]>([])
  const [selectedId, setSelectedId] = useState("")
  const [baseModelId, setBaseModelId] = useState<string>("absa-v2b")
  const [trainingConfig, setTrainingConfig] = useState<TrainingConfig>({})

  const loadForm = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [cfg, defaults, rows] = await Promise.all([
        fetchPipelineConfig(),
        fetchDefaultTrainingConfig().catch(() => ({ training_config: {} as TrainingConfig })),
        fetchDatasets(),
      ])
      setConfig(cfg)
      setTrainingConfig(defaults.training_config ?? cfg.default_training_config ?? {})
      setDatasets(rows)
      const preferred =
        rows.find((d) => d.audit_passed && d.status !== "failed") ??
        rows.find((d) => d.audit_passed) ??
        rows[0]
      setSelectedId(preferred?.dataset_id ?? "")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không tải được cấu hình pipeline.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (open) loadForm()
  }, [open, loadForm])

  const canStart =
    Boolean(selectedId) &&
    Boolean(config?.configured) &&
    !config?.demo_mode &&
    !busy &&
    !loading

  const updateConfig = (key: TrainingConfigField, value: string) => {
    const numeric = Number(value)
    setTrainingConfig((prev) => ({
      ...prev,
      [key]: Number.isFinite(numeric) ? numeric : value,
    }))
  }

  const onStart = async () => {
    if (!selectedId) return
    setBusy(true)
    setError(null)
    try {
      const run = await triggerPipeline({
        dataset_id: selectedId,
        base_model_id: baseModelId,
        training_config: trainingConfig,
        requested_by: "console-ui",
      })
      const normalized: PipelineRun = {
        execution_arn: run.execution_arn,
        name: run.name ?? run.run_id ?? "run",
        status: run.status ?? "RUNNING",
        start_date: run.start_date ?? new Date().toISOString(),
        stop_date: run.stop_date ?? null,
        dataset_id: run.dataset_id ?? selectedId,
        dataset_key: run.dataset_key ?? null,
        dataset_s3_uri: run.dataset_s3_uri ?? null,
        run_id: run.run_id,
        base_model_id: run.base_model_id ?? baseModelId,
        candidate_model_id: run.candidate_model_id,
        code_version: run.code_version,
        training_source_uri: run.training_source_uri,
        training_config: run.training_config ?? trainingConfig,
        stages: run.stages ?? [],
      }
      onStarted?.(normalized)
      setOpen(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không khởi động được pipeline.")
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Button size="sm" onClick={() => setOpen(true)}>
        <Plus className="size-3.5" />
        New run
      </Button>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-lg">
          <SheetHeader>
            <SheetTitle>New training run</SheetTitle>
            <SheetDescription>
              Chọn dataset, base model, và hyperparameters. Code train được pin theo version đã deploy — không cần commit mỗi lần chạy.
            </SheetDescription>
          </SheetHeader>

          <div className="flex flex-col gap-4 px-4 pb-4">
            {loading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                Đang tải…
              </div>
            ) : null}

            {config?.demo_mode ? (
              <p className="rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-muted-foreground">
                Pipeline chưa cấu hình Step Functions trên backend. Chạy Deploy Runtime với state machine.
              </p>
            ) : null}

            {datasets.length === 0 && !loading ? (
              <p className="text-sm text-muted-foreground">
                Chưa có dataset.{" "}
                <Link href={appPath("/datasets")} className="text-link hover:underline">
                  Upload dataset
                </Link>{" "}
                trước.
              </p>
            ) : null}

            {datasets.length > 0 ? (
              <label className="space-y-2 text-sm">
                <span className="text-muted-foreground">Dataset</span>
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={selectedId}
                  onChange={(e) => setSelectedId(e.target.value)}
                  disabled={busy}
                >
                  {datasets.map((d) => (
                    <option key={d.dataset_id} value={d.dataset_id}>
                      {d.name} · {d.total_rows} rows
                      {d.audit_passed ? " · audited" : ""}
                      {d.status === "failed" ? " · failed" : ""}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}

            <label className="space-y-2 text-sm">
              <span className="text-muted-foreground">Base model (so sánh)</span>
              <select
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono"
                value={baseModelId}
                onChange={(e) => setBaseModelId(e.target.value)}
                disabled={busy}
              >
                {BASE_MODEL_OPTIONS.map((id) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </select>
            </label>

            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Training config</p>
              <div className="grid gap-3 sm:grid-cols-2">
                {TRAINING_CONFIG_FIELDS.map((key) => (
                  <label key={key} className="text-xs">
                    {key}
                    <Input
                      className="mt-1 font-mono text-xs"
                      type="number"
                      step="any"
                      value={String(trainingConfig[key] ?? "")}
                      onChange={(e) => updateConfig(key, e.target.value)}
                      disabled={busy}
                    />
                  </label>
                ))}
              </div>
            </div>

            {error ? <p className="text-sm text-destructive">{error}</p> : null}
          </div>

          <SheetFooter>
            <Button className="w-full gap-2" disabled={!canStart} onClick={onStart}>
              {busy ? <Loader2 className="size-4 animate-spin" /> : <PlayCircle className="size-4" />}
              Start training
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </>
  )
}
