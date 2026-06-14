"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { Loader2, Plus } from "lucide-react"

import { ConsoleShell } from "@/components/layout/console-shell"
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
import { Button } from "@/components/ui/button"
import { fetchPipelineRuns } from "@/lib/api/pipeline"
import { formatDuration, formatF1 } from "@/lib/console/format"
import type { PipelineRun } from "@/types/pipeline"

function runBestF1(run: PipelineRun): number | null {
  if (run.best_f1 != null) return run.best_f1
  const metric = run.evaluation?.metrics?.tas_relaxed_f1 ?? run.evaluation?.metrics?.global_f1
  return metric != null ? metric : null
}

function runModel(run: PipelineRun): string {
  return run.candidate_model_id ?? run.training_config?.model_name?.split("/").pop() ?? "absa-v1"
}

function runDataset(run: PipelineRun): string {
  return run.dataset_id ?? run.dataset_key?.split("/").pop() ?? "—"
}

export default function TrainingRunsPage() {
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [datasetFilter, setDatasetFilter] = useState("all")
  const [sort, setSort] = useState("newest")

  useEffect(() => {
    fetchPipelineRuns(25)
      .then((res) => {
        setRuns(res.runs)
        if (res.runs.length === 0) {
          setNotice("Chưa có training run nào. Kết nối Step Functions hoặc trigger pipeline để bắt đầu.")
        }
      })
      .catch((err) => {
        setRuns([])
        setNotice(err instanceof Error ? err.message : "Không tải được training runs.")
      })
      .finally(() => setLoading(false))
  }, [])

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
          actions={
            <Button size="sm" disabled>
              <Plus className="size-3.5" />
              New run
            </Button>
          }
        />

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
                            href={`/training-runs/${encodeURIComponent(run.execution_arn)}`}
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
