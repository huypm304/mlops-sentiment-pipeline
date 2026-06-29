"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { Loader2 } from "lucide-react"

import {
  AliasPill,
  AuditPill,
  PlatformMetadataLine,
  RegistryLink,
  RegistryPageHeader,
  RegistrySurface,
  RegistryTable,
  RegistryTd,
  RegistryTh,
  RegistryThead,
  RegistryTr,
  RunNameCell,
  RunStatusCell,
} from "@/components/console/registry"
import { ConsoleShell } from "@/components/layout/console-shell"
import { Button } from "@/components/ui/button"
import { fetchAnalytics } from "@/lib/api/analytics"
import { fetchDatasets } from "@/lib/api/datasets"
import { fetchModels } from "@/lib/api/metrics"
import { fetchHealth, fetchMonitoring } from "@/lib/api/runtime"
import { fetchPipelineRuns } from "@/lib/api/pipeline"
import { datasetAuditLabel } from "@/lib/console/format"
import { datasetDetailPath, modelDetailPath, trainingRunDetailPath } from "@/lib/console/paths"
import type { ModelSummary } from "@/lib/constants/metrics"
import type { DatasetListItem } from "@/types/dataset"
import type { PipelineRun } from "@/types/pipeline"

export default function HomePage() {
  const [datasets, setDatasets] = useState<DatasetListItem[]>([])
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [models, setModels] = useState<ModelSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [apiHealth, setApiHealth] = useState("unknown")
  const [predictions24h, setPredictions24h] = useState(0)
  const [lowConf, setLowConf] = useState(0)
  const [driftStatus, setDriftStatus] = useState("unknown")

  useEffect(() => {
    Promise.all([
      fetchDatasets().catch(() => []),
      fetchPipelineRuns(8)
        .then((res) => res.runs)
        .catch(() => []),
      fetchModels().catch(() => []),
      fetchHealth()
        .then((h) => setApiHealth(h.endpoint_health))
        .catch(() => setApiHealth("unknown")),
      fetchAnalytics(24)
        .then((a) => {
          setPredictions24h(a.summary.predictions)
          setLowConf(a.summary.low_confidence_rate)
        })
        .catch(() => null),
      fetchMonitoring()
        .then((m) => setDriftStatus(m.drift.status))
        .catch(() => null),
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

  if (loading) {
    return (
      <ConsoleShell>
        <div className="flex items-center gap-2 py-16 text-[13px] text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Loading workspace…
        </div>
      </ConsoleShell>
    )
  }

  const metaLine = [
    `API ${apiHealth}`,
    `${predictions24h} predictions (24h)`,
    productionModel ? `Champion ${productionModel.version}` : "No champion",
    `Drift ${driftStatus.replace(/_/g, " ")}`,
    `Low confidence ${lowConf.toFixed(1)}%`,
  ].join(" · ")

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <RegistryPageHeader
          title="Workspace overview"
          metadata={
            <>
              <PlatformMetadataLine />
              <p className="mt-0.5">{metaLine}</p>
            </>
          }
          actions={
            <>
              <Button variant="outline" size="sm" asChild>
                <Link href="/datasets">Register dataset</Link>
              </Button>
              <Button variant="outline" size="sm" asChild>
                <Link href="/inference">Test inference</Link>
              </Button>
              <Button size="sm" asChild>
                <Link href="/training-runs">Training runs</Link>
              </Button>
            </>
          }
        />

        <div className="grid gap-4 xl:grid-cols-2">
          <RegistrySurface>
            <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
              <p className="text-[13px] font-semibold">Datasets</p>
              <RegistryLink href="/datasets">View all</RegistryLink>
            </div>
            <RegistryTable>
              <RegistryThead>
                <tr>
                  <RegistryTh>Dataset</RegistryTh>
                  <RegistryTh>Status</RegistryTh>
                  <RegistryTh align="right">Samples</RegistryTh>
                  <RegistryTh>Audit</RegistryTh>
                </tr>
              </RegistryThead>
              <tbody>
                {datasets.slice(0, 5).map((row) => (
                  <RegistryTr key={row.dataset_id}>
                    <RegistryTd>
                      <RegistryLink href={datasetDetailPath(row.dataset_id)}>
                        {row.name}
                      </RegistryLink>
                    </RegistryTd>
                    <RegistryTd muted className="capitalize">
                      {row.status}
                    </RegistryTd>
                    <RegistryTd align="right" numeric>
                      {row.total_rows.toLocaleString()}
                    </RegistryTd>
                    <RegistryTd>
                      <AuditPill
                        label={datasetAuditLabel(
                          row.audit_status ?? (row.audit_passed ? "pass" : "pending"),
                          row.audit_passed,
                        )}
                      />
                    </RegistryTd>
                  </RegistryTr>
                ))}
              </tbody>
            </RegistryTable>
          </RegistrySurface>

          <RegistrySurface>
            <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
              <p className="text-[13px] font-semibold">Training runs</p>
              <RegistryLink href="/training-runs">View all</RegistryLink>
            </div>
            <RegistryTable>
              <RegistryThead>
                <tr>
                  <RegistryTh>Run</RegistryTh>
                  <RegistryTh>Status</RegistryTh>
                  <RegistryTh>Dataset</RegistryTh>
                </tr>
              </RegistryThead>
              <tbody>
                {runs.slice(0, 5).map((run) => (
                  <RegistryTr key={run.execution_arn}>
                    <RegistryTd>
                      <RunNameCell
                        name={run.run_id ?? run.name}
                        href={trainingRunDetailPath(run.run_id ?? run.name)}
                        status={run.status}
                      />
                    </RegistryTd>
                    <RegistryTd>
                      <RunStatusCell status={run.status} timestamp={run.start_date} />
                    </RegistryTd>
                    <RegistryTd mono muted>
                      {run.dataset_id ?? run.dataset_key ?? "—"}
                    </RegistryTd>
                  </RegistryTr>
                ))}
              </tbody>
            </RegistryTable>
          </RegistrySurface>
        </div>

        {productionModel ? (
          <RegistrySurface>
            <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
              <p className="text-[13px] font-semibold">Production model</p>
              <RegistryLink href={modelDetailPath(productionModel.version)}>
                Open registry
              </RegistryLink>
            </div>
            <RegistryTable>
              <RegistryThead>
                <tr>
                  <RegistryTh>Name</RegistryTh>
                  <RegistryTh>Alias</RegistryTh>
                  <RegistryTh align="right">TAS F1</RegistryTh>
                  <RegistryTh>Checkpoint</RegistryTh>
                </tr>
              </RegistryThead>
              <tbody>
                <RegistryTr>
                  <RegistryTd>
                    <RegistryLink href={modelDetailPath(productionModel.version)}>
                      {productionModel.version}
                    </RegistryLink>
                  </RegistryTd>
                  <RegistryTd>
                    <AliasPill alias={productionModel.alias ?? "Champion"} />
                  </RegistryTd>
                  <RegistryTd align="right" numeric>
                    {(productionModel.tas_relaxed_f1 * 100).toFixed(1)}%
                  </RegistryTd>
                  <RegistryTd mono muted>
                    {productionModel.checkpoint}
                  </RegistryTd>
                </RegistryTr>
              </tbody>
            </RegistryTable>
          </RegistrySurface>
        ) : null}
      </section>
    </ConsoleShell>
  )
}
