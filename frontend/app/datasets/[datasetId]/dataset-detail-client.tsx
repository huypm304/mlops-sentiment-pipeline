"use client"

import Link from "next/link"

import { appPath } from "@/lib/console/paths"
import { useEffect, useMemo, useState } from "react"
import { Loader2, PlayCircle } from "lucide-react"

import { ConsoleShell } from "@/components/layout/console-shell"
import { SectionHeader } from "@/components/console/section-header"
import { StatusBadge } from "@/components/console/status-badge"
import { TableCard, ConsoleTable, ConsoleThead, ConsoleTh, ConsoleTr, ConsoleTd } from "@/components/console/table-card"
import { Button } from "@/components/ui/button"
import { fetchDataset, auditDataset } from "@/lib/api/datasets"
import type { DatasetManifest } from "@/types/dataset"

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
      await auditDataset(datasetId)
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
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{auditError}</p>
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

            <div className="space-y-4">
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

              <div className="rounded-md border border-border bg-card">
                <div className="border-b border-border px-4 py-3">
                  <p className="text-sm font-semibold">Audit report</p>
                </div>
                <div className="space-y-2 px-4 py-4 text-sm">
                  {Object.keys(dataset.audits).length === 0 ? (
                    <p className="text-muted-foreground">No audit report attached.</p>
                  ) : (
                    Object.entries(dataset.audits).map(([split, audit]) => (
                      <div key={split} className="rounded border border-border px-3 py-2">
                        <p className="text-xs uppercase tracking-wide text-muted-foreground">{split}</p>
                        <p className="font-mono text-xs">Report: {audit.report_id}</p>
                        <p className="text-xs text-muted-foreground">Score: {Math.round(audit.audit_score * 100)}%</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </section>
    </ConsoleShell>
  )
}
