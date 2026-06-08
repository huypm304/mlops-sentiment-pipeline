"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"

import { ConsoleShell } from "@/components/layout/console-shell"
import { SectionHeader } from "@/components/console/section-header"
import { TableCard, ConsoleTable, ConsoleThead, ConsoleTh, ConsoleTr, ConsoleTd } from "@/components/console/table-card"
import { StatusBadge } from "@/components/console/status-badge"
import { fetchDatasets } from "@/lib/api/datasets"
import { fetchModels } from "@/lib/api/metrics"
import { fetchPipelineRuns } from "@/lib/api/pipeline"
import type { DatasetListItem } from "@/types/dataset"
import type { PipelineRun } from "@/types/pipeline"
import type { ModelSummary } from "@/lib/constants/metrics"

const quickActions = [
  { label: "Upload dataset", href: "/datasets" },
  { label: "Start training", href: "/training-runs" },
  { label: "View models", href: "/models" },
  { label: "Open inference", href: "/inference" },
]

export default function HomePage() {
  const [datasets, setDatasets] = useState<DatasetListItem[]>([])
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [models, setModels] = useState<ModelSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetchDatasets().catch(() => []),
      fetchPipelineRuns(8).then((res) => res.runs).catch(() => []),
      fetchModels().catch(() => []),
    ])
      .then(([d, r, m]) => {
        setDatasets(d)
        setRuns(r)
        setModels(m)
      })
      .finally(() => setLoading(false))
  }, [])

  const productionModel = useMemo(
    () => models.find((m) => m.status === "production") ?? models[0] ?? null,
    [models],
  )

  return (
    <ConsoleShell>
      <section className="space-y-6">
        <SectionHeader
          title="Welcome"
          description="Operational workspace for ABSA datasets, runs, models, inference, and monitoring."
        />

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md border border-border bg-card px-4 py-3 text-sm font-medium transition-colors hover:bg-muted/30"
            >
              {item.label}
            </Link>
          ))}
        </div>

        <section className="grid gap-6 xl:grid-cols-[2fr_1fr]">
          <div className="space-y-6">
            <TableCard
              title="Recent datasets"
              loading={loading}
              loadingLabel="Loading datasets"
              empty={!loading && datasets.length === 0}
              emptyLabel="No datasets found."
            >
              <ConsoleTable>
                <ConsoleThead>
                  <tr>
                    <ConsoleTh>Dataset</ConsoleTh>
                    <ConsoleTh>Status</ConsoleTh>
                    <ConsoleTh align="right">Rows</ConsoleTh>
                    <ConsoleTh align="right">Audit</ConsoleTh>
                  </tr>
                </ConsoleThead>
                <tbody>
                  {datasets.slice(0, 6).map((row) => (
                    <ConsoleTr key={row.dataset_id}>
                      <ConsoleTd>
                        <Link href={`/datasets/${encodeURIComponent(row.dataset_id)}`} className="font-medium hover:underline">
                          {row.name}
                        </Link>
                      </ConsoleTd>
                      <ConsoleTd><StatusBadge value={row.status} /></ConsoleTd>
                      <ConsoleTd align="right" numeric>{row.total_rows.toLocaleString()}</ConsoleTd>
                      <ConsoleTd align="right" numeric>
                        {row.audit_score == null ? "-" : `${Math.round(row.audit_score * 100)}%`}
                      </ConsoleTd>
                    </ConsoleTr>
                  ))}
                </tbody>
              </ConsoleTable>
            </TableCard>

            <TableCard
              title="Recent training runs"
              loading={loading}
              loadingLabel="Loading runs"
              empty={!loading && runs.length === 0}
              emptyLabel="No runs found."
            >
              <ConsoleTable>
                <ConsoleThead>
                  <tr>
                    <ConsoleTh>Run</ConsoleTh>
                    <ConsoleTh>Status</ConsoleTh>
                    <ConsoleTh>Start</ConsoleTh>
                  </tr>
                </ConsoleThead>
                <tbody>
                  {runs.slice(0, 6).map((run) => (
                    <ConsoleTr key={run.execution_arn}>
                      <ConsoleTd>
                        <Link
                          href={`/training-runs/${encodeURIComponent(run.execution_arn)}`}
                          className="font-medium hover:underline"
                        >
                          {run.run_id ?? run.name}
                        </Link>
                      </ConsoleTd>
                      <ConsoleTd><StatusBadge value={run.status} /></ConsoleTd>
                      <ConsoleTd muted>
                        {run.start_date ? new Date(run.start_date).toLocaleString() : "-"}
                      </ConsoleTd>
                    </ConsoleTr>
                  ))}
                </tbody>
              </ConsoleTable>
            </TableCard>
          </div>

          <div className="rounded-md border border-border bg-card">
            <div className="border-b border-border px-4 py-3">
              <h2 className="text-sm font-semibold">Current production model</h2>
            </div>
            {!productionModel ? (
              <p className="px-4 py-6 text-sm text-muted-foreground">No model found.</p>
            ) : (
              <div className="space-y-2 px-4 py-4 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-muted-foreground">Version</span>
                  <span className="font-mono">{productionModel.version}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-muted-foreground">Status</span>
                  <StatusBadge value={productionModel.status} />
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-muted-foreground">Global F1</span>
                  <span className="tabular-nums">{(productionModel.global_f1 * 100).toFixed(1)}%</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-muted-foreground">TAS Relaxed F1</span>
                  <span className="tabular-nums">{(productionModel.tas_relaxed_f1 * 100).toFixed(1)}%</span>
                </div>
                <div className="pt-2">
                  <Link href={`/models/${encodeURIComponent(productionModel.version)}`} className="text-sm font-medium text-primary hover:underline">
                    View model detail
                  </Link>
                </div>
              </div>
            )}
          </div>
        </section>
      </section>
    </ConsoleShell>
  )
}
