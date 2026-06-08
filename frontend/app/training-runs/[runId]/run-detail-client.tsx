"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { Loader2 } from "lucide-react"

import { ConsoleShell } from "@/components/layout/console-shell"
import { SectionHeader } from "@/components/console/section-header"
import { StatusBadge } from "@/components/console/status-badge"
import { fetchPipelineRun } from "@/lib/api/pipeline"
import type { PipelineRun } from "@/types/pipeline"

const tabs = ["Overview", "Parameters", "Metrics", "Artifacts", "Logs", "Comparison", "Decision"] as const

type RunTab = (typeof tabs)[number]

export function RunDetailClient({ runId }: { runId: string }) {
  const [activeTab, setActiveTab] = useState<RunTab>("Overview")
  const [run, setRun] = useState<PipelineRun | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPipelineRun(runId)
      .then(setRun)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load run detail"))
      .finally(() => setLoading(false))
  }, [runId])

  const tabBody = useMemo(() => {
    if (!run) return null

    if (activeTab === "Overview") {
      return (
        <div className="space-y-2 text-sm">
          <Row label="Run ID" value={run.run_id ?? run.name} mono />
          <div className="flex items-center justify-between gap-3 rounded border border-border/70 px-3 py-2">
            <span className="text-muted-foreground">Status</span>
            <StatusBadge value={run.status} />
          </div>
          <Row label="Dataset" value={run.dataset_key ?? "-"} mono />
          <Row label="Start" value={run.start_date ? new Date(run.start_date).toLocaleString() : "-"} />
          <Row label="Stop" value={run.stop_date ? new Date(run.stop_date).toLocaleString() : "-"} />
        </div>
      )
    }

    if (activeTab === "Parameters") {
      return <JsonBlock value={run.training_config ?? { note: "No parameters captured" }} />
    }

    if (activeTab === "Metrics") {
      return <JsonBlock value={run.evaluation?.metrics ?? { note: "No metrics available" }} />
    }

    if (activeTab === "Artifacts") {
      return <JsonBlock value={{ dataset_key: run.dataset_key, execution_arn: run.execution_arn }} />
    }

    if (activeTab === "Logs") {
      return <JsonBlock value={{ stages: run.sfn_steps ?? run.stages }} />
    }

    if (activeTab === "Comparison") {
      return <JsonBlock value={run.comparison ?? { note: "No comparison available" }} />
    }

    return <JsonBlock value={{ approval_id: run.approval_id, decision: run.status }} />
  }, [activeTab, run])

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <SectionHeader title="Run detail" description={runId}>
          <Link href="/training-runs" className="text-xs text-muted-foreground hover:underline">Back to runs</Link>
        </SectionHeader>

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading run detail
          </div>
        ) : error ? (
          <p className="text-sm text-red-500">{error}</p>
        ) : !run ? (
          <p className="text-sm text-muted-foreground">Run not found.</p>
        ) : (
          <div className="rounded-md border border-border bg-card">
            <div className="flex flex-wrap gap-2 border-b border-border px-4 py-3">
              {tabs.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setActiveTab(tab)}
                  className={`rounded border px-2.5 py-1 text-xs ${activeTab === tab ? "border-primary text-primary" : "border-border text-muted-foreground"}`}
                >
                  {tab}
                </button>
              ))}
            </div>
            <div className="p-4">{tabBody}</div>
          </div>
        )}
      </section>
    </ConsoleShell>
  )
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded border border-border/70 px-3 py-2">
      <span className="text-muted-foreground">{label}</span>
      <span className={mono ? "font-mono text-xs" : ""}>{value}</span>
    </div>
  )
}

function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="overflow-x-auto rounded border border-border/70 bg-background p-3 text-xs text-muted-foreground">
      {JSON.stringify(value, null, 2)}
    </pre>
  )
}
