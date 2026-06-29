"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { Loader2 } from "lucide-react"

import { ActivePipelineRunPanel } from "@/components/active-pipeline-run-panel"
import { isActiveRunStatus } from "@/components/pipeline-stage-stepper"
import { ConsoleShell } from "@/components/layout/console-shell"
import { NewTrainingRunSheet } from "@/components/console/new-training-run-sheet"
import {
  PlatformMetadataLine,
  RegistryEmpty,
  RegistryPageHeader,
  RegistrySurface,
  RegistryTable,
  RegistryTd,
  RegistryTh,
  RegistryThead,
  RegistryToolbar,
  RegistryTr,
  RunNameCell,
  RunStatusCell,
} from "@/components/console/registry"
import { fetchPipelineRuns } from "@/lib/api/pipeline"
import { trainingRunDetailPath } from "@/lib/console/paths"
import { formatDuration, formatF1 } from "@/lib/console/format"
import type { PipelineRun } from "@/types/pipeline"

function runBestF1(run: PipelineRun): number | null {
  if (run.best_f1 != null) return run.best_f1
  const fromEval =
    run.evaluation?.metrics?.tas_relaxed_f1 ??
    run.evaluation?.metrics?.global_f1
  if (fromEval != null) return fromEval
  const fromMetrics = run.metrics?.tas_relaxed_f1 ?? run.metrics?.global_f1
  return fromMetrics != null ? fromMetrics : null
}

function runModel(run: PipelineRun): string {
  return run.candidate_model_id ?? run.training_config?.model_name?.split("/").pop() ?? "absa-v1"
}

function runDataset(run: PipelineRun): string {
  return run.dataset_id ?? run.dataset_key?.split("/").pop() ?? "—"
}

export default function TrainingRunsPage() {
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [activeRun, setActiveRun] = useState<PipelineRun | null>(null)
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [datasetFilter, setDatasetFilter] = useState("all")
  const [sort, setSort] = useState("newest")

  const loadRuns = useCallback(() => {
    setLoading(true)
    fetchPipelineRuns(25)
      .then((res) => {
        setRuns(res.runs)
        setNotice(
          res.runs.length === 0
            ? "Chưa có training run nào. Bấm New run để trigger pipeline."
            : null,
        )
      })
      .catch((err) => {
        setRuns([])
        setNotice(err instanceof Error ? err.message : "Không tải được training runs.")
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    loadRuns()
  }, [loadRuns])

  const hasActiveRun = useMemo(
    () =>
      runs.some((r) => isActiveRunStatus(r.status)) ||
      (activeRun != null && isActiveRunStatus(activeRun.status)),
    [runs, activeRun],
  )

  useEffect(() => {
    const fromList = runs.find((r) => isActiveRunStatus(r.status))
    if (fromList) {
      setActiveRun((prev) => (prev?.run_id === fromList.run_id ? prev : fromList))
    } else if (activeRun && !isActiveRunStatus(activeRun.status)) {
      setActiveRun(null)
    }
  }, [runs, activeRun])

  useEffect(() => {
    if (!hasActiveRun) return
    const id = setInterval(() => {
      fetchPipelineRuns(25)
        .then((res) => setRuns(res.runs))
        .catch(() => undefined)
    }, 3000)
    return () => clearInterval(id)
  }, [hasActiveRun])

  const onRunStarted = useCallback(
    (run: PipelineRun) => {
      setActiveRun(run)
      setRuns((prev) => [run, ...prev.filter((r) => r.execution_arn !== run.execution_arn)])
      setNotice(null)
    },
    [],
  )

  const datasetOptions = useMemo(() => {
    const ids = [...new Set(runs.map(runDataset).filter((v) => v !== "—"))]
    return [{ label: "All datasets", value: "all" }, ...ids.map((id) => ({ label: id, value: id }))]
  }, [runs])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    let rows = runs.filter((run) => {
      const id = (run.run_id ?? run.name).toLowerCase()
      const dataset = runDataset(run).toLowerCase()
      const model = runModel(run).toLowerCase()
      const status = run.status.toLowerCase()
      if (statusFilter !== "all" && status !== statusFilter) return false
      if (datasetFilter !== "all" && runDataset(run) !== datasetFilter) return false
      if (!q) return true
      return id.includes(q) || dataset.includes(q) || model.includes(q)
    })

    rows = [...rows].sort((a, b) => {
      const ta = new Date(a.start_date ?? 0).getTime()
      const tb = new Date(b.start_date ?? 0).getTime()
      return sort === "newest" ? tb - ta : ta - tb
    })

    return rows
  }, [runs, search, statusFilter, datasetFilter, sort])

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <RegistryPageHeader
          title="Training Runs"
          metadata={<PlatformMetadataLine />}
          actions={<NewTrainingRunSheet onStarted={onRunStarted} />}
        />

        {activeRun && isActiveRunStatus(activeRun.status) ? (
          <ActivePipelineRunPanel
            run={activeRun}
            onUpdate={(detail) => {
              setActiveRun(detail)
              setRuns((prev) =>
                prev.map((r) => ((r.run_id ?? r.name) === (detail.run_id ?? detail.name) ? detail : r)),
              )
            }}
            onCancelled={() => setActiveRun(null)}
          />
        ) : null}

        {loading ? (
          <div className="flex items-center gap-2 py-8 text-[13px] text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading runs…
          </div>
        ) : (
          <RegistrySurface
            notice={notice}
            toolbar={
              <RegistryToolbar
                search={search}
                onSearchChange={setSearch}
                searchPlaceholder="Filter runs by name, dataset, or model"
                filters={[
                  {
                    label: "Status",
                    value: statusFilter,
                    onChange: setStatusFilter,
                    options: [
                      { label: "All", value: "all" },
                      { label: "Succeeded", value: "succeeded" },
                      { label: "Running", value: "running" },
                      { label: "Failed", value: "failed" },
                    ],
                  },
                  {
                    label: "Dataset",
                    value: datasetFilter,
                    onChange: setDatasetFilter,
                    options: datasetOptions,
                  },
                  {
                    label: "Sort",
                    value: sort,
                    onChange: setSort,
                    options: [
                      { label: "Created (newest)", value: "newest" },
                      { label: "Created (oldest)", value: "oldest" },
                    ],
                  },
                ]}
              />
            }
          >
            {filtered.length === 0 ? (
              <RegistryEmpty
                title="No runs logged"
                description="Start a training run or adjust filters to see pipeline executions."
              />
            ) : (
              <RegistryTable>
                <RegistryThead>
                  <tr>
                    <RegistryTh>Run name</RegistryTh>
                    <RegistryTh>Status</RegistryTh>
                    <RegistryTh>Dataset</RegistryTh>
                    <RegistryTh>Model</RegistryTh>
                    <RegistryTh>Duration</RegistryTh>
                    <RegistryTh align="right">Best F1</RegistryTh>
                    <RegistryTh>Artifact</RegistryTh>
                  </tr>
                </RegistryThead>
                <tbody>
                  {filtered.map((run) => {
                    const bestF1 = runBestF1(run)
                    const duration =
                      run.duration_seconds ??
                      (run.start_date && run.stop_date
                        ? Math.max(
                            Math.floor(
                              (new Date(run.stop_date).getTime() - new Date(run.start_date).getTime()) /
                                1000,
                            ),
                            0,
                          )
                        : null)
                    const runName = run.run_id ?? run.name

                    return (
                      <RegistryTr key={run.execution_arn}>
                        <RegistryTd>
                          <RunNameCell
                            name={runName}
                            href={trainingRunDetailPath(run.run_id ?? run.name)}
                            status={run.status}
                          />
                        </RegistryTd>
                        <RegistryTd>
                          <RunStatusCell status={run.status} timestamp={run.start_date} />
                        </RegistryTd>
                        <RegistryTd mono>{runDataset(run)}</RegistryTd>
                        <RegistryTd mono>{runModel(run)}</RegistryTd>
                        <RegistryTd muted mono>
                          {formatDuration(duration)}
                        </RegistryTd>
                        <RegistryTd align="right" numeric>
                          {formatF1(bestF1)}
                        </RegistryTd>
                        <RegistryTd className="max-w-[160px] truncate">
                          {run.artifact_uri ? (
                            <span className="text-link font-mono text-[12px]">{run.artifact_uri}</span>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </RegistryTd>
                      </RegistryTr>
                    )
                  })}
                </tbody>
              </RegistryTable>
            )}
          </RegistrySurface>
        )}
      </section>
    </ConsoleShell>
  )
}
