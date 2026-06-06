"use client"

import { useCallback, useEffect, useState } from "react"
import { Loader2, PlayCircle, RefreshCw } from "lucide-react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { fetchLatestAuditReport, runDatasetAudit } from "@/lib/api/audit"
import type { AuditBenchmark, AuditReport } from "@/types/audit"

function BenchmarkRow({ row }: { row: AuditBenchmark }) {
  return (
    <tr className="border-b border-border/60 last:border-0">
      <td className="py-3 pr-4 font-medium">{row.name}</td>
      <td className="hidden py-3 pr-4 text-muted-foreground md:table-cell">{row.description}</td>
      <td className="py-3 pr-4 font-mono text-sm">{row.display_value}</td>
      <td className="py-3 pr-4 text-muted-foreground">{row.display_threshold}</td>
      <td className="py-3">
        <Badge variant={row.status === "pass" ? "default" : "destructive"}>{row.status}</Badge>
      </td>
    </tr>
  )
}

/** Fixed order — matches training schema (all 7 aspects always shown). */
const ASPECT_ORDER = [
  "Fashion",
  "Electronics",
  "General",
  "Service",
  "Ship",
  "Price",
  "App",
] as const

function distToChart(data: Record<string, number>) {
  return Object.entries(data).map(([name, value]) => ({ name, value }))
}

function aspectDistToChart(data: Record<string, number>) {
  return ASPECT_ORDER.map((name) => ({ name, value: data[name] ?? 0 }))
}

function DatasetSelect({
  value,
  onChange,
}: {
  value: "train" | "demo"
  onChange: (v: "train" | "demo") => void
}) {
  return (
    <select
      className="rounded-md border border-input bg-background px-3 py-2 text-sm"
      value={value}
      onChange={(e) => onChange(e.target.value as "train" | "demo")}
    >
      <option value="train">data_train.jsonl</option>
      <option value="demo">demo_10.jsonl</option>
    </select>
  )
}

export function AuditDashboard() {
  const [report, setReport] = useState<AuditReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [dataset, setDataset] = useState<"train" | "demo">("train")

  const load = useCallback(async () => {
    setError(null)
    try {
      setReport(await fetchLatestAuditReport())
    } catch (err) {
      setReport(null)
      setError(err instanceof Error ? err.message : "Failed to load audit report")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleRun = async () => {
    setRunning(true)
    setError(null)
    try {
      await runDatasetAudit(dataset)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Audit failed")
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading audit report…
      </div>
    )
  }

  if (!report) {
    return (
      <div className="space-y-4">
        {error && <p className="text-sm text-destructive">{error}</p>}
        <EmptyState
          title="No audit report yet"
          description="Run a VLSP-style quality audit on your training JSONL before retraining."
        />
        <div className="flex flex-wrap items-center gap-2">
          <DatasetSelect value={dataset} onChange={setDataset} />
          <Button onClick={handleRun} disabled={running}>
            {running ? <Loader2 className="mr-2 size-4 animate-spin" /> : <PlayCircle className="mr-2 size-4" />}
            Run audit
          </Button>
        </div>
      </div>
    )
  }

  const aspectData = aspectDistToChart(report.distributions.aspects)
  const sentimentData = distToChart(report.distributions.opinion_sentiments)

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={report.passed ? "default" : "destructive"}>
              {report.passed ? "Passed" : "Failed"}
            </Badge>
            <span className="font-mono text-xs text-muted-foreground">{report.report_id}</span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {report.source_label} · {new Date(report.generated_at).toLocaleString()}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <DatasetSelect value={dataset} onChange={setDataset} />
          <Button variant="outline" size="sm" onClick={load} disabled={running}>
            <RefreshCw className="mr-2 size-4" />
            Refresh
          </Button>
          <Button size="sm" onClick={handleRun} disabled={running}>
            {running ? <Loader2 className="mr-2 size-4 animate-spin" /> : <PlayCircle className="mr-2 size-4" />}
            Re-run audit
          </Button>
        </div>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Records", value: report.summary.parsed_records },
          { label: "Opinions", value: report.summary.total_opinions },
          { label: "Errors", value: report.summary.error_count },
          { label: "Warnings", value: report.summary.warning_count },
        ].map((s) => (
          <Card key={s.label} size="sm">
            <CardHeader>
              <CardDescription>{s.label}</CardDescription>
              <CardTitle className="text-2xl tabular-nums">{s.value}</CardTitle>
            </CardHeader>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quality benchmarks</CardTitle>
          <CardDescription>
            VLSP / ABSA schema gates — training should pass before admin approval
          </CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b text-muted-foreground">
                <th className="pb-2 font-medium">Benchmark</th>
                <th className="hidden pb-2 font-medium md:table-cell">Description</th>
                <th className="pb-2 font-medium">Result</th>
                <th className="pb-2 font-medium">Threshold</th>
                <th className="pb-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {report.benchmarks.map((row) => (
                <BenchmarkRow key={row.id} row={row} />
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Aspect distribution</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={aspectData} margin={{ top: 8, right: 8, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border/50" />
                <XAxis
                  dataKey="name"
                  interval={0}
                  tick={{ fontSize: 10 }}
                  angle={-35}
                  textAnchor="end"
                  height={56}
                />
                <YAxis tick={{ fontSize: 11 }} width={48} />
                <Tooltip />
                <Bar dataKey="value" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Opinion sentiment distribution</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sentimentData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border/50" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" fill="var(--chart-2)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {report.issues.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Issues sample</CardTitle>
            <CardDescription>
              {report.issue_truncated ? "Showing first 500 issues" : `${report.issues.length} issues`}
            </CardDescription>
          </CardHeader>
          <CardContent className="max-h-80 overflow-y-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="pb-2 pr-3">Line</th>
                  <th className="pb-2 pr-3">Code</th>
                  <th className="pb-2 pr-3">Severity</th>
                  <th className="pb-2">Message</th>
                </tr>
              </thead>
              <tbody>
                {report.issues.slice(0, 50).map((issue, i) => (
                  <tr key={`${issue.line}-${issue.code}-${i}`} className="border-b border-border/40">
                    <td className="py-2 pr-3 font-mono">{issue.line}</td>
                    <td className="py-2 pr-3 font-mono text-xs">{issue.code}</td>
                    <td className="py-2 pr-3">
                      <Badge variant={issue.severity === "error" ? "destructive" : "outline"}>
                        {issue.severity}
                      </Badge>
                    </td>
                    <td className="py-2 text-muted-foreground">{issue.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
