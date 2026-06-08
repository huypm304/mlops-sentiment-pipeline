"use client"

import Link from "next/link"
import { useEffect, useRef, useState } from "react"
import { Loader2, Upload, X } from "lucide-react"

import { ConsoleShell } from "@/components/layout/console-shell"
import { SectionHeader } from "@/components/console/section-header"
import { TableCard, ConsoleTable, ConsoleThead, ConsoleTh, ConsoleTr, ConsoleTd } from "@/components/console/table-card"
import { StatusBadge } from "@/components/console/status-badge"
import { Button } from "@/components/ui/button"
import { fetchDatasets, uploadDatasetBundle, auditDataset } from "@/lib/api/datasets"
import type { DatasetListItem } from "@/types/dataset"

export default function DatasetsPage() {
  const [rows, setRows] = useState<DatasetListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showUpload, setShowUpload] = useState(false)

  function reload() {
    setLoading(true)
    fetchDatasets()
      .then(setRows)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load datasets"))
      .finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <SectionHeader title="Datasets" description="Registry and audit status.">
          <Button size="sm" onClick={() => setShowUpload(true)}>
            <Upload className="mr-1.5 size-3.5" />
            Upload dataset
          </Button>
        </SectionHeader>

        {showUpload && (
          <UploadSheet
            onClose={() => setShowUpload(false)}
            onSuccess={() => { setShowUpload(false); reload() }}
          />
        )}

        <TableCard
          title="Dataset registry"
          loading={loading}
          loadingLabel="Loading datasets"
          error={error}
          empty={!loading && !error && rows.length === 0}
          emptyLabel="No datasets found."
        >
          <ConsoleTable>
            <ConsoleThead>
              <tr>
                <ConsoleTh>Dataset</ConsoleTh>
                <ConsoleTh>Status</ConsoleTh>
                <ConsoleTh>Splits</ConsoleTh>
                <ConsoleTh align="right">Rows</ConsoleTh>
                <ConsoleTh align="right">Audit</ConsoleTh>
                <ConsoleTh>Created</ConsoleTh>
              </tr>
            </ConsoleThead>
            <tbody>
              {rows.map((row) => (
                <ConsoleTr key={row.dataset_id}>
                  <ConsoleTd>
                    <Link href={`/datasets/${encodeURIComponent(row.dataset_id)}`} className="font-medium hover:underline">
                      {row.name}
                    </Link>
                    <p className="font-mono text-xs text-muted-foreground">{row.dataset_id}</p>
                  </ConsoleTd>
                  <ConsoleTd><StatusBadge value={row.status} /></ConsoleTd>
                  <ConsoleTd muted>{row.splits.join(", ")}</ConsoleTd>
                  <ConsoleTd align="right" numeric>{row.total_rows.toLocaleString()}</ConsoleTd>
                  <ConsoleTd align="right" numeric>
                    {row.audit_score == null ? "-" : `${Math.round(row.audit_score * 100)}%`}
                  </ConsoleTd>
                  <ConsoleTd muted>
                    {row.created_at ? new Date(row.created_at).toLocaleString() : "-"}
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

function UploadSheet({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [name, setName] = useState("")
  const [trainFile, setTrainFile] = useState<File | null>(null)
  const [devFile, setDevFile] = useState<File | null>(null)
  const [testFile, setTestFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const trainRef = useRef<HTMLInputElement>(null)
  const devRef = useRef<HTMLInputElement>(null)
  const testRef = useRef<HTMLInputElement>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) { setUploadError("Dataset name is required."); return }
    if (!trainFile) { setUploadError("Train file is required."); return }
    if (!devFile) { setUploadError("Dev file is required."); return }
    setUploadError(null)
    setSubmitting(true)
    try {
      const manifest = await uploadDatasetBundle({ name: name.trim(), train: trainFile, dev: devFile, test: testFile })
      // kick off audit immediately — failures are non-fatal
      try { await auditDataset(manifest.dataset_id) } catch { /* ignore */ }
      onSuccess()
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end">
      <div className="absolute inset-0 bg-black/20" onClick={onClose} />
      <aside className="relative z-10 flex h-full w-full max-w-md flex-col border-l border-border bg-background shadow-xl">
        <header className="flex items-center justify-between border-b border-border px-5 py-4">
          <h2 className="text-sm font-semibold">Upload dataset</h2>
          <button type="button" onClick={onClose} className="rounded p-1 hover:bg-muted">
            <X className="size-4" />
          </button>
        </header>

        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-5 overflow-y-auto p-5">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground" htmlFor="ds-name">Dataset name *</label>
            <input
              id="ds-name"
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              placeholder="e.g. absa-v8-kaggle"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <FileField label="Train file (.jsonl) *" accept=".jsonl,.json,.csv" fileRef={trainRef} file={trainFile} onChange={setTrainFile} />
          <FileField label="Dev file (.jsonl) *" accept=".jsonl,.json,.csv" fileRef={devRef} file={devFile} onChange={setDevFile} />
          <FileField label="Test file (.jsonl) — optional" accept=".jsonl,.json,.csv" fileRef={testRef} file={testFile} onChange={setTestFile} />

          {uploadError && (
            <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{uploadError}</p>
          )}

          <div className="mt-auto flex gap-2">
            <Button type="button" variant="outline" className="flex-1" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" className="flex-1" disabled={submitting}>
              {submitting ? <><Loader2 className="mr-1.5 size-3.5 animate-spin" />Uploading &amp; auditing…</> : "Upload"}
            </Button>
          </div>
        </form>
      </aside>
    </div>
  )
}

function FileField({
  label,
  accept,
  fileRef,
  file,
  onChange,
}: {
  label: string
  accept: string
  fileRef: React.RefObject<HTMLInputElement | null>
  file: File | null
  onChange: (f: File | null) => void
}) {
  return (
    <div className="space-y-1.5">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <div
        className="flex cursor-pointer items-center gap-2 rounded-md border border-dashed border-border px-3 py-2.5 text-sm text-muted-foreground hover:border-primary hover:text-foreground"
        onClick={() => fileRef.current?.click()}
      >
        <Upload className="size-4 shrink-0" />
        <span className="truncate">{file ? file.name : "Click to select file"}</span>
        {file && (
          <button
            type="button"
            className="ml-auto shrink-0 rounded p-0.5 hover:bg-muted"
            onClick={(e) => { e.stopPropagation(); onChange(null); if (fileRef.current) fileRef.current.value = "" }}
          >
            <X className="size-3" />
          </button>
        )}
      </div>
      <input
        ref={fileRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => onChange(e.target.files?.[0] ?? null)}
      />
    </div>
  )
}
