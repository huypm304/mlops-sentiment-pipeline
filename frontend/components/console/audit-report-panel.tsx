import { StatusBadge } from "@/components/console/status-badge"
import {
  ConsoleTable,
  ConsoleTd,
  ConsoleTh,
  ConsoleThead,
  ConsoleTr,
} from "@/components/console/table-card"
import type { AuditBenchmark, AuditIssue } from "@/types/audit"
import type { SplitAuditInfo } from "@/types/dataset"
import { cn } from "@/lib/utils"

const ASPECT_ORDER = [
  "Fashion",
  "Electronics",
  "General",
  "Service",
  "Ship",
  "Price",
  "App",
] as const

function distRows(data: Record<string, number> | undefined, order?: readonly string[]) {
  if (!data) return []
  const keys = order?.length ? order : Object.keys(data)
  const max = Math.max(...keys.map((k) => data[k] ?? 0), 1)
  return keys
    .map((name) => ({ name, value: data[name] ?? 0, pct: ((data[name] ?? 0) / max) * 100 }))
    .filter((row) => row.value > 0)
}

export function AuditReportPanel({ audit }: { audit: SplitAuditInfo }) {
  const benchmarks = audit.benchmarks ?? []
  const issues = audit.issues ?? []
  const aspectRows = distRows(audit.distributions?.aspects, ASPECT_ORDER)
  const opinionRows = distRows(audit.distributions?.opinion_sentiments)
  const globalRows = distRows(audit.distributions?.global_sentiments)

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <StatusBadge value={audit.passed ? "pass" : audit.data_level_status ?? "fail"} />
        <span className="font-mono text-muted-foreground">{audit.report_id}</span>
        <span className="text-muted-foreground">Score {Math.round(audit.audit_score * 100)}%</span>
        {audit.generated_at ? (
          <span className="text-muted-foreground">
            · {new Date(audit.generated_at).toLocaleString()}
          </span>
        ) : null}
      </div>

      {audit.summary ? (
        <dl className="grid grid-cols-2 gap-2 text-[12px] sm:grid-cols-3 lg:grid-cols-6">
          {[
            { label: "Train rows", value: audit.summary.train_rows },
            { label: "Dev rows", value: audit.summary.dev_rows },
            { label: "Parsed", value: audit.summary.parsed_records },
            { label: "Opinions", value: audit.summary.total_opinions },
            { label: "Warnings", value: audit.summary.warning_count },
            { label: "Errors", value: audit.error_count },
          ].map((row) => (
            <div key={row.label} className="rounded border border-border/70 px-2.5 py-2">
              <dt className="text-[10px] uppercase tracking-wide text-muted-foreground">{row.label}</dt>
              <dd className="mt-0.5 font-mono text-sm tabular-nums">
                {row.value != null ? row.value.toLocaleString() : "—"}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}

      {benchmarks.length > 0 ? (
        <section className="space-y-2">
          <p className="text-[12px] font-semibold">Data benchmark modules</p>
          <ConsoleTable>
            <ConsoleThead>
              <tr>
                <ConsoleTh>Module</ConsoleTh>
                <ConsoleTh className="hidden lg:table-cell">Description</ConsoleTh>
                <ConsoleTh>Result</ConsoleTh>
                <ConsoleTh>Threshold</ConsoleTh>
                <ConsoleTh>Status</ConsoleTh>
              </tr>
            </ConsoleThead>
            <tbody>
              {benchmarks.map((row) => (
                <AuditBenchmarkRow key={row.id} row={row} />
              ))}
            </tbody>
          </ConsoleTable>
        </section>
      ) : null}

      {aspectRows.length > 0 || opinionRows.length > 0 || globalRows.length > 0 ? (
        <div className="grid gap-4 lg:grid-cols-3">
          <DistributionCard title="Aspect distribution" rows={aspectRows} />
          <DistributionCard title="Opinion sentiment" rows={opinionRows} />
          <DistributionCard title="Global sentiment" rows={globalRows} />
        </div>
      ) : null}

      {issues.length > 0 ? (
        <section className="space-y-2">
          <p className="text-[12px] font-semibold">
            Issues
            {audit.issue_truncated ? (
              <span className="ml-1 font-normal text-muted-foreground">(showing first {issues.length})</span>
            ) : null}
          </p>
          <ConsoleTable>
            <ConsoleThead>
              <tr>
                <ConsoleTh>Line</ConsoleTh>
                <ConsoleTh>Code</ConsoleTh>
                <ConsoleTh>Severity</ConsoleTh>
                <ConsoleTh>Message</ConsoleTh>
              </tr>
            </ConsoleThead>
            <tbody>
              {issues.map((issue, idx) => (
                <IssueRow key={`${issue.line}-${issue.code}-${idx}`} issue={issue} />
              ))}
            </tbody>
          </ConsoleTable>
        </section>
      ) : null}

      {!audit.passed && audit.failed_checks && audit.failed_checks.length > 0 ? (
        <p className="rounded border border-red-500/30 bg-red-500/10 px-3 py-2 text-[12px] text-red-700 dark:text-red-300">
          Failed modules: {audit.failed_checks.join(", ")}
        </p>
      ) : null}
    </div>
  )
}

function DistributionCard({
  title,
  rows,
}: {
  title: string
  rows: { name: string; value: number; pct: number }[]
}) {
  if (rows.length === 0) return null
  return (
    <div className="rounded border border-border/70 p-3">
      <p className="text-[11px] font-semibold">{title}</p>
      <ul className="mt-2 space-y-1.5">
        {rows.map((row) => (
          <li key={row.name} className="space-y-0.5">
            <div className="flex items-center justify-between gap-2 text-[11px]">
              <span className="truncate text-muted-foreground">{row.name}</span>
              <span className="shrink-0 font-mono tabular-nums">{row.value.toLocaleString()}</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-muted/50">
              <div
                className="h-full rounded-full bg-primary/70"
                style={{ width: `${row.pct}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

function AuditBenchmarkRow({ row }: { row: AuditBenchmark }) {
  return (
    <ConsoleTr>
      <ConsoleTd>{row.name}</ConsoleTd>
      <ConsoleTd muted className="hidden max-w-[260px] lg:table-cell">
        {row.description}
      </ConsoleTd>
      <ConsoleTd mono>{row.display_value}</ConsoleTd>
      <ConsoleTd muted>{row.display_threshold}</ConsoleTd>
      <ConsoleTd>
        <StatusBadge value={row.status} />
      </ConsoleTd>
    </ConsoleTr>
  )
}

function IssueRow({ issue }: { issue: AuditIssue }) {
  return (
    <ConsoleTr>
      <ConsoleTd mono>{issue.line}</ConsoleTd>
      <ConsoleTd mono muted>{issue.code}</ConsoleTd>
      <ConsoleTd>
        <StatusBadge
          value={issue.severity}
          className={cn(issue.severity === "error" && "border-red-500/40")}
        />
      </ConsoleTd>
      <ConsoleTd muted className="max-w-[320px]">
        {issue.message}
      </ConsoleTd>
    </ConsoleTr>
  )
}
