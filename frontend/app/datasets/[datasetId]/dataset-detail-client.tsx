"use client"

import Link from "next/link"

import { appPath } from "@/lib/console/paths"
import { useEffect, useMemo, useState } from "react"
import { Loader2, PlayCircle } from "lucide-react"

import { AuditReportPanel } from "@/components/console/audit-report-panel"
import { ConsoleShell } from "@/components/layout/console-shell"
import { SectionHeader } from "@/components/console/section-header"
import { StatusBadge } from "@/components/console/status-badge"
import { TableCard, ConsoleTable, ConsoleThead, ConsoleTh, ConsoleTr, ConsoleTd } from "@/components/console/table-card"
import { Button } from "@/components/ui/button"
import { fetchDataset, auditDataset } from "@/lib/api/datasets"
import type { DatasetAuditResponse, DatasetManifest, SplitAuditInfo } from "@/types/dataset"

function auditFromResponse(response: DatasetAuditResponse): SplitAuditInfo {
  const summary = response.summary ?? {}
  return {
    report_id: response.report_id,
    passed: response.passed,
    audit_score: response.audit_score ?? 0,
    error_count: Number(summary.error_count ?? 0),
    generated_at: new Date().toISOString(),
    data_level_status: response.data_level_status,
    failed_checks: (response.benchmarks ?? [])
      .filter((row) => row.status === "fail")
      .map((row) => row.name),
    benchmarks: response.benchmarks ?? [],
    distributions: response.distributions,
    issues: response.issues ?? [],
    issue_truncated: response.issue_truncated,
    summary: {
      train_rows: Number(summary.train_rows ?? 0),
      dev_rows: Number(summary.dev_rows ?? 0),
      warning_count: Number(summary.warning_count ?? 0),
      parsed_records: Number(summary.parsed_records ?? 0),
      total_opinions: Number(summary.total_opinions ?? 0),
      avg_opinions_per_record: Number(summary.avg_opinions_per_record ?? 0),
    },
  }
}

export function DatasetDetailClient({ datasetId }: { datasetId: string }) {
  const [dataset, setDataset] = useState<DatasetManifest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [auditing, setAuditing] = useState(false)
  const [auditError, setAuditError] = useState<string | null>(null)

  function reload() {
    setLoading(true)
    fetchDataset(datasetId)
      .then(setDataset)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load dataset"))
      .finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [datasetId]) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleAudit() {
    setAuditing(true)
    setAuditError(null)
    try {
      const response = await auditDataset(datasetId)
      const bundle = auditFromResponse(response)
      setDataset((current) =>
        current
          ? {
              ...current,
              audit_passed: response.passed,
              status: response.passed ? "audited" : "failed",
              updated_at: new Date().toISOString(),
              audits: { bundle },
            }
          : current,
      )
      reload()
    } catch (err) {
      setAuditError(err instanceof Error ? err.message : "Audit failed")
    } finally {
      setAuditing(false)
    }
  }

  const splitRows = useMemo(() => {
    if (!dataset) return []
    return Object.entries(dataset.splits)
  }, [dataset])

  const bundleAudit = dataset?.audits?.bundle

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <SectionHeader title="Dataset detail" description={datasetId}>
          <div className="flex items-center gap-2">
            <Link href={appPath("/datasets")} className="text-xs text-muted-foreground hover:underline">
              Back to datasets
            </Link>
            {dataset && dataset.status !== "approved" && (
              <Button size="sm" onClick={handleAudit} disabled={auditing}>
                {auditing
                  ? <><Loader2 className="mr-1.5 size-3.5 animate-spin" />Running…</>
                  : <><PlayCircle className="mr-1.5 size-3.5" />Run audit</>}
              </Button>
            )}
          </div>
        </SectionHeader>

        {auditError && (
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
            {auditError}
          </p>
        )}

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading dataset
          </div>
        ) : error ? (
          <p className="text-sm text-red-500">{error}</p>
        ) : !dataset ? (
          <p className="text-sm text-muted-foreground">Dataset not found.</p>
        ) : (
          <>
            <div className="grid gap-4 xl:grid-cols-[1.3fr_1fr]">
              <TableCard title="Manifest" empty={splitRows.length === 0} emptyLabel="No split metadata found.">
                <ConsoleTable>
                  <ConsoleThead>
                    <tr>
                      <ConsoleTh>Split</ConsoleTh>
                      <ConsoleTh>Filename</ConsoleTh>
                      <ConsoleTh align="right">Rows</ConsoleTh>
                      <ConsoleTh align="right">Size</ConsoleTh>
                    </tr>
                  </ConsoleThead>
                  <tbody>
                    {splitRows.map(([split, meta]) => (
                      <ConsoleTr key={split}>
                        <ConsoleTd className="uppercase tracking-wide">{split}</ConsoleTd>
                        <ConsoleTd mono>{meta.filename}</ConsoleTd>
                        <ConsoleTd align="right" numeric>{meta.rows.toLocaleString()}</ConsoleTd>
                        <ConsoleTd align="right" numeric>{Math.round(meta.size_bytes / 1024)} KB</ConsoleTd>
                      </ConsoleTr>
                    ))}
                  </tbody>
                </ConsoleTable>
              </TableCard>

              <div className="rounded-md border border-border bg-card">
                <div className="border-b border-border px-4 py-3">
                  <p className="text-sm font-semibold">Approval status</p>
                </div>
                <div className="space-y-2 px-4 py-4 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Status</span>
                    <StatusBadge value={dataset.status} />
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Audit passed</span>
                    <span>{dataset.audit_passed ? "Yes" : "No"}</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Updated</span>
                    <span className="text-right text-xs">{new Date(dataset.updated_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </div>

            <TableCard
              title="Audit report"
              empty={!bundleAudit}
              emptyLabel="No audit report yet. Run audit after upload."
            >
              {bundleAudit ? <AuditReportPanel audit={bundleAudit} /> : null}
            </TableCard>
          </>
        )}
      </section>
    </ConsoleShell>
  )
}
