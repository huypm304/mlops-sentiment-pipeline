"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Loader2, Upload, X } from "lucide-react"

import { ConsoleShell } from "@/components/layout/console-shell"
import {
  AuditPill,
  PlatformMetadataLine,
  RegistryEmpty,
  RegistryLink,
  RegistryPageHeader,
  RegistrySurface,
  RegistryTable,
  RegistryTd,
  RegistryTh,
  RegistryThead,
  RegistryToolbar,
  RegistryTr,
} from "@/components/console/registry"
import { Button } from "@/components/ui/button"
import { fetchDatasets, uploadDatasetBundle, auditDataset } from "@/lib/api/datasets"
import { datasetAuditLabel } from "@/lib/console/format"
import type { DatasetListItem } from "@/types/dataset"

export default function DatasetsPage() {
  const [rows, setRows] = useState<DatasetListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState<string | null>(null)
  const [showUpload, setShowUpload] = useState(false)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [auditFilter, setAuditFilter] = useState("all")

  function reload() {
    setLoading(true)
    setNotice(null)
    fetchDatasets()
      .then((datasets) => {
        setRows(datasets)
        if (datasets.length === 0) {
          setNotice("Chưa có dataset nào. Upload train/dev/test JSONL để bắt đầu.")
        }
      })
      .catch((err) => {
        setRows([])
        setNotice(err instanceof Error ? err.message : "Không tải được datasets.")
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    reload()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return rows.filter((row) => {
      const audit = row.audit_status ?? (row.audit_passed ? "pass" : "pending")
      if (statusFilter !== "all" && row.status !== statusFilter) return false
      if (auditFilter !== "all" && audit !== auditFilter) return false
      if (!q) return true
      return row.name.toLowerCase().includes(q) || row.dataset_id.toLowerCase().includes(q)
    })
  }, [rows, search, statusFilter, auditFilter])

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <RegistryPageHeader
          title="Dataset Registry"
          metadata={<PlatformMetadataLine />}
          actions={
            <Button size="sm" onClick={() => setShowUpload(true)}>
              <Upload className="size-3.5" />
              Upload dataset
            </Button>
          }
        />

        {showUpload && (
          <UploadSheet
            onClose={() => setShowUpload(false)}
            onSuccess={() => {
              setShowUpload(false)
              reload()
            }}
          />
        )}

        {loading ? (
          <div className="flex items-center gap-2 py-8 text-[13px] text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading datasets…
          </div>
        ) : (
          <RegistrySurface
            notice={notice}
            toolbar={
              <RegistryToolbar
                search={search}
                onSearchChange={setSearch}
                searchPlaceholder="Filter datasets by name"
                filters={[
                  {
                    label: "Status",
                    value: statusFilter,
                    onChange: setStatusFilter,
                    options: [
                      { label: "All", value: "all" },
                      { label: "Approved", value: "approved" },
                      { label: "Audited", value: "audited" },
                      { label: "Pending", value: "pending" },
                    ],
                  },
                  {
                    label: "Audit",
                    value: auditFilter,
                    onChange: setAuditFilter,
                    options: [
                      { label: "All", value: "all" },
                      { label: "Pass", value: "pass" },
                      { label: "Running", value: "running" },
                      { label: "Pending", value: "pending" },
                    ],
                  },
                ]}
              />
            }
          >
            {filtered.length === 0 ? (
              <RegistryEmpty
                title="No datasets registered"
                description="Upload train/dev/test JSONL splits to start auditing and training."
                action={
                  <Button size="sm" onClick={() => setShowUpload(true)}>
                    Upload dataset
                  </Button>
                }
              />
            ) : (
              <RegistryTable>
                <RegistryThead>
                  <tr>
                    <RegistryTh>Dataset</RegistryTh>
                    <RegistryTh>Status</RegistryTh>
                    <RegistryTh align="right">Samples</RegistryTh>
                    <RegistryTh>Audit</RegistryTh>
                    <RegistryTh>Splits</RegistryTh>
                  </tr>
                </RegistryThead>
                <tbody>
                  {filtered.map((row) => {
                    const auditStatus = row.audit_status ?? (row.audit_passed ? "pass" : "pending")
                    const auditLabel = datasetAuditLabel(auditStatus, row.audit_passed)
                    return (
                      <RegistryTr key={row.dataset_id}>
                        <RegistryTd>
                          <RegistryLink href={`/datasets/${encodeURIComponent(row.dataset_id)}`}>
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
                          <AuditPill label={auditLabel} />
                        </RegistryTd>
                        <RegistryTd muted>{row.splits.join(", ")}</RegistryTd>
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
    if (!name.trim()) {
      setUploadError("Dataset name is required.")
      return
    }
    if (!trainFile) {
      setUploadError("Train file is required.")
      return
    }
    if (!devFile) {
      setUploadError("Dev file is required.")
      return
    }
    setUploadError(null)
    setSubmitting(true)
    try {
      const manifest = await uploadDatasetBundle({
        name: name.trim(),
        train: trainFile,
        dev: devFile,
        test: testFile,
      })
      const audit = await auditDataset(manifest.dataset_id)
      if (!audit.passed) {
        setUploadError("Upload finished but audit failed — open the dataset to review the report.")
      }
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
            <label className="text-xs font-medium text-muted-foreground" htmlFor="ds-name">
              Dataset name *
            </label>
            <input
              id="ds-name"
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              placeholder="e.g. absa-v8-kaggle"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <FileField
            label="Train file (.jsonl) *"
            accept=".jsonl,.json,.csv"
            fileRef={trainRef}
            file={trainFile}
            onChange={setTrainFile}
          />
          <FileField
            label="Dev file (.jsonl) *"
            accept=".jsonl,.json,.csv"
            fileRef={devRef}
            file={devFile}
            onChange={setDevFile}
          />
          <FileField
            label="Test file (.jsonl) — optional"
            accept=".jsonl,.json,.csv"
            fileRef={testRef}
            file={testFile}
            onChange={setTestFile}
          />

          {uploadError && (
            <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {uploadError}
            </p>
          )}

          <div className="mt-auto flex gap-2">
            <Button type="button" variant="outline" className="flex-1" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" className="flex-1" disabled={submitting}>
              {submitting ? (
                <>
                  <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                  Uploading &amp; auditing…
                </>
              ) : (
                "Upload"
              )}
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
            onClick={(e) => {
              e.stopPropagation()
              onChange(null)
              if (fileRef.current) fileRef.current.value = ""
            }}
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
