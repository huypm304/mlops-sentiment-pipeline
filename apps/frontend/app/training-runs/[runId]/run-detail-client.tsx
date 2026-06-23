"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import { Loader2 } from "lucide-react"

import { ConsoleShell } from "@/components/layout/console-shell"
import { SectionHeader } from "@/components/console/section-header"
import { StatusBadge } from "@/components/console/status-badge"
import { fetchPipelineRun } from "@/lib/api/pipeline"
import { formatF1 } from "@/lib/console/format"
import type { PipelineRun } from "@/types/pipeline"

const tabs = ["Overview", "Parameters", "Metrics", "Artifacts", "Comparison", "Decision"] as const

type RunTab = (typeof tabs)[number]

const ACTIVE_STATUSES = new Set(["RUNNING", "TRAINING", "TRAINING_IN_PROGRESS", "EVALUATED", "COMPARED"])

function isActiveStatus(status: string) {
  return ACTIVE_STATUSES.has(status.toUpperCase())
}

export function RunDetailClient({ runId }: { runId: string }) {
  const [activeTab, setActiveTab] = useState<RunTab>("Overview")
  const [run, setRun] = useState<PipelineRun | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadRun = useCallback(async () => {
    try {
      const detail = await fetchPipelineRun(runId)
      setRun(detail)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load run detail")
    } finally {
      setLoading(false)
    }
  }, [runId])

  useEffect(() => {
    setLoading(true)
    loadRun()
  }, [loadRun])

  useEffect(() => {
    if (!run || !isActiveStatus(run.status)) return
    const id = setInterval(loadRun, 5000)
    return () => clearInterval(id)
  }, [run?.status, loadRun, run])

  const tabBody = useMemo(() => {
    if (!run) return null

    if (activeTab === "Overview") {
      const bestF1 =
        run.best_f1 ??
        run.evaluation?.metrics?.tas_relaxed_f1 ??
        run.metrics?.tas_relaxed_f1 ??
        run.evaluation?.metrics?.global_f1

      return (
        <div className="space-y-4 text-sm">
          <Row label="Run ID" value={run.run_id ?? run.name} mono />
          <div className="flex items-center justify-between gap-3 rounded border border-border/70 px-3 py-2">
            <span className="text-muted-foreground">Status</span>
            <StatusBadge value={run.status} />
          </div>
          <Row label="Best F1" value={formatF1(bestF1 ?? null)} />
          <Row label="Base model" value={run.base_model_id ?? "—"} mono />
          <Row label="Candidate" value={run.candidate_model_id ?? "—"} mono />
          <Row label="Start" value={run.start_date ? new Date(run.start_date).toLocaleString() : "-"} />
          <Row label="Stop" value={run.stop_date ? new Date(run.stop_date).toLocaleString() : "-"} />

          <LineageBlock title="Code version" rows={[
            ["code_version", run.code_version ?? "—"],
            ["training_source_uri", run.training_source_uri ?? "—"],
          ]} />
          <LineageBlock title="Data version" rows={[
            ["dataset_id", run.dataset_id ?? "—"],
            ["dataset_key", run.dataset_key ?? "—"],
            ["dataset_s3_uri", run.dataset_s3_uri ?? "—"],
          ]} />
          <LineageBlock title="Experiment config" rows={[
            ["epochs", String(run.training_config?.epochs ?? "—")],
            ["batch_size", String(run.training_config?.batch_size ?? "—")],
            ["lr_backbone", String(run.training_config?.lr_backbone ?? "—")],
          ]} />
        </div>
      )
    }

    if (activeTab === "Parameters") {
      return <JsonBlock value={run.training_config ?? { note: "No parameters captured" }} />
    }

    if (activeTab === "Metrics") {
      const metrics = run.evaluation?.metrics ?? run.metrics
      return metrics && Object.keys(metrics).length > 0 ? (
        <JsonBlock value={metrics} />
      ) : (
        <JsonBlock value={{ note: "No metrics yet — pipeline may still be running" }} />
      )
    }

    if (activeTab === "Artifacts") {
      return (
        <JsonBlock
          value={{
            artifact_uri: run.artifact_uri,
            production_uri: run.production_uri,
            dataset_s3_uri: run.dataset_s3_uri,
            execution_arn: run.execution_arn,
          }}
        />
      )
    }

    if (activeTab === "Comparison") {
      return run.comparison ? (
        <JsonBlock value={run.comparison} />
      ) : (
        <JsonBlock value={{ note: "Comparison available after Evaluate + Compare stages" }} />
      )
    }

    return (
      <JsonBlock
        value={{
          approval_id: run.approval_id,
          outcome: run.status,
          promote: run.comparison?.promote,
          registry_status: (run as PipelineRun & { registry_status?: string }).registry_status,
        }}
      />
    )
  }, [activeTab, run])

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <SectionHeader title="Run detail" description={run?.run_id ?? runId}>
          <Link href="/training-runs" className="text-xs text-muted-foreground hover:underline">
            Back to runs
          </Link>
        </SectionHeader>

        {loading && !run ? (
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
            {isActiveStatus(run.status) ? (
              <div className="flex items-center gap-2 border-b border-border px-4 py-2 text-xs text-muted-foreground">
                <Loader2 className="size-3 animate-spin" />
                Pipeline running — auto-refresh every 5s
              </div>
            ) : null}
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
      <span className={`${mono ? "font-mono text-xs" : ""} max-w-[65%] truncate text-right`}>{value}</span>
    </div>
  )
}

function LineageBlock({
  title,
  rows,
}: {
  title: string
  rows: [string, string][]
}) {
  return (
    <div className="rounded border border-border/70 p-3">
      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">{title}</p>
      <div className="space-y-1">
        {rows.map(([key, value]) => (
          <div key={key} className="flex justify-between gap-2 text-xs">
            <span className="text-muted-foreground">{key}</span>
            <span className="max-w-[70%] truncate font-mono text-right">{value}</span>
          </div>
        ))}
      </div>
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
