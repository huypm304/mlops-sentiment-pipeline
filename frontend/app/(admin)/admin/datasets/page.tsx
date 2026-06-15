"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import { CheckCircle2, Loader2, PlayCircle, Upload } from "lucide-react"

import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { auditDataset, fetchDatasets, uploadDatasetBundle } from "@/lib/api/datasets"
import type { DatasetListItem } from "@/types/dataset"
import { cn } from "@/lib/utils"

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-500/10 text-amber-400",
  audited: "bg-blue-500/10 text-blue-400",
  approved: "bg-emerald-500/10 text-emerald-400",
}

function FileInput({
  id,
  label,
  required,
  onChange,
}: {
  id: string
  label: string
  required?: boolean
  onChange: (file: File | null) => void
}) {
  return (
    <label className="block space-y-1.5">
      <span className="text-[12px] font-medium text-muted-foreground">
        {label}
        {!required ? " (optional)" : ""}
      </span>
      <input
        id={id}
        type="file"
        accept=".jsonl,application/jsonl"
        required={required}
        className="block w-full text-[12px] file:mr-3 file:rounded-md file:border-0 file:bg-muted file:px-3 file:py-1.5 file:text-[12px] file:font-medium"
        onChange={(e) => onChange(e.target.files?.[0] ?? null)}
      />
    </label>
  )
}

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<DatasetListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState("")
  const [trainFile, setTrainFile] = useState<File | null>(null)
  const [devFile, setDevFile] = useState<File | null>(null)
  const [testFile, setTestFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [auditingId, setAuditingId] = useState<string | null>(null)

  const load = useCallback(async () => {
    setError(null)
    try {
      setDatasets(await fetchDatasets())
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load datasets")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || !trainFile || !devFile) return

    setUploading(true)
    setError(null)
    try {
      await uploadDatasetBundle({
        name: name.trim(),
        train: trainFile,
        dev: devFile,
        test: testFile,
      })
      setName("")
      setTrainFile(null)
      setDevFile(null)
      setTestFile(null)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed")
    } finally {
      setUploading(false)
    }
  }

  async function handleAudit(datasetId: string) {
    setAuditingId(datasetId)
    setError(null)
    try {
      await auditDataset(datasetId)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Audit failed")
    } finally {
      setAuditingId(null)
    }
  }

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-[15px] font-semibold tracking-tight">Datasets</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Upload train / dev / test JSONL, then run VLSP audit benchmarks before training
        </p>
      </header>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <form
        onSubmit={handleUpload}
        className="rounded-lg border border-border/60 bg-card p-4 space-y-4"
      >
        <div className="flex items-center gap-2">
          <Upload className="size-4 text-muted-foreground" />
          <p className="text-[13px] font-medium">Upload dataset bundle</p>
        </div>

        <label className="block space-y-1.5">
          <span className="text-[12px] font-medium text-muted-foreground">Dataset name</span>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="absa-v4-release"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </label>

        <div className="grid gap-3 sm:grid-cols-3">
          <FileInput id="train-file" label="Train" required onChange={setTrainFile} />
          <FileInput id="dev-file" label="Dev" required onChange={setDevFile} />
          <FileInput id="test-file" label="Test" onChange={setTestFile} />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button type="submit" size="sm" disabled={uploading || !name.trim() || !trainFile || !devFile}>
            {uploading ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
            Upload bundle
          </Button>
          <p className="text-[11px] text-muted-foreground">
            Requires train + dev JSONL. Test is optional but recommended for benchmark coverage.
          </p>
        </div>
      </form>

      <div className="rounded-lg border border-border/60 bg-card">
        <div className="border-b border-border/60 px-4 py-2.5">
          <p className="text-[12px] font-medium uppercase tracking-wider text-muted-foreground">
            Registered datasets
          </p>
        </div>

        {loading ? (
          <div className="flex items-center gap-2 px-4 py-8 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading datasets…
          </div>
        ) : datasets.length === 0 ? (
          <div className="px-4 py-8">
            <EmptyState
              title="No datasets uploaded"
              description="Upload train and dev JSONL files to register a dataset for audit."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/40 text-[11px] text-muted-foreground">
                  <th className="px-4 py-2 text-left font-medium">Dataset</th>
                  <th className="px-4 py-2 text-left font-medium">Status</th>
                  <th className="px-4 py-2 text-left font-medium">Splits</th>
                  <th className="px-4 py-2 text-right font-medium">Rows</th>
                  <th className="px-4 py-2 text-right font-medium">Audit score</th>
                  <th className="px-4 py-2 text-left font-medium">Created</th>
                  <th className="px-4 py-2 text-left font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((row) => (
                  <tr key={row.dataset_id} className="border-b border-border/20 last:border-0">
                    <td className="px-4 py-2.5">
                      <p className="font-medium">{row.name}</p>
                      <p className="font-mono text-[11px] text-muted-foreground">{row.dataset_id}</p>
                    </td>
                    <td className="px-4 py-2.5">
                      <span
                        className={cn(
                          "rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase",
                          STATUS_STYLES[row.status] ?? "bg-muted text-muted-foreground",
                        )}
                      >
                        {row.status}
                      </span>
                      {row.audit_passed ? (
                        <CheckCircle2 className="mt-1 size-3.5 text-emerald-400" />
                      ) : null}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-[11px]">{row.splits.join(", ")}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums">{row.total_rows.toLocaleString()}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-[12px] tabular-nums">
                      {row.audit_score != null ? `${(row.audit_score * 100).toFixed(0)}%` : "—"}
                    </td>
                    <td className="px-4 py-2.5 text-[12px] text-muted-foreground">
                      {row.created_at ? new Date(row.created_at).toLocaleString() : "—"}
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={auditingId === row.dataset_id}
                          onClick={() => handleAudit(row.dataset_id)}
                        >
                          {auditingId === row.dataset_id ? (
                            <Loader2 className="size-4 animate-spin" />
                          ) : (
                            <PlayCircle className="size-4" />
                          )}
                          Audit all
                        </Button>
                        <Button size="sm" variant="ghost" asChild>
                          <Link href={`/admin/audit?dataset=${encodeURIComponent(row.dataset_id)}`}>
                            View report
                          </Link>
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
