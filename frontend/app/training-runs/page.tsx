"use client"

import Link from "next/link"
import { useEffect, useState } from "react"

import { ConsoleShell } from "@/components/layout/console-shell"
import { SectionHeader } from "@/components/console/section-header"
import { TableCard, ConsoleTable, ConsoleThead, ConsoleTh, ConsoleTr, ConsoleTd } from "@/components/console/table-card"
import { StatusBadge } from "@/components/console/status-badge"
import { fetchPipelineRuns } from "@/lib/api/pipeline"
import type { PipelineRun } from "@/types/pipeline"

export default function TrainingRunsPage() {
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPipelineRuns(25)
      .then((res) => setRuns(res.runs))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load runs"))
      .finally(() => setLoading(false))
  }, [])

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <SectionHeader title="Training Runs" description="MLflow-style run tracking table." />

        <TableCard
          title="Runs"
          loading={loading}
          loadingLabel="Loading runs"
          error={error}
          empty={!loading && !error && runs.length === 0}
          emptyLabel="No runs found."
        >
          <ConsoleTable>
            <ConsoleThead>
              <tr>
                <ConsoleTh>Run</ConsoleTh>
                <ConsoleTh>Status</ConsoleTh>
                <ConsoleTh>Dataset</ConsoleTh>
                <ConsoleTh>Stage</ConsoleTh>
                <ConsoleTh>Start</ConsoleTh>
              </tr>
            </ConsoleThead>
            <tbody>
              {runs.map((run) => (
                <ConsoleTr key={run.execution_arn}>
                  <ConsoleTd>
                    <Link href={`/training-runs/${encodeURIComponent(run.execution_arn)}`} className="font-medium hover:underline">
                      {run.run_id ?? run.name}
                    </Link>
                    <p className="font-mono text-xs text-muted-foreground">{run.execution_arn.slice(0, 56)}…</p>
                  </ConsoleTd>
                  <ConsoleTd><StatusBadge value={run.status} /></ConsoleTd>
                  <ConsoleTd mono muted>{run.dataset_key ?? "-"}</ConsoleTd>
                  <ConsoleTd muted>{run.current_stage ?? "-"}</ConsoleTd>
                  <ConsoleTd muted>
                    {run.start_date ? new Date(run.start_date).toLocaleString() : "-"}
                  </ConsoleTd>
                </ConsoleTr>
              ))}
            </tbody>
          </ConsoleTable>
        </TableCard>
      </section>
    </ConsoleShell>
  )
}
