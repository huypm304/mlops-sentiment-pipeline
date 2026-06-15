export type BenchmarkStatus = "pass" | "fail" | "warn"

export interface AuditBenchmark {
  id: string
  name: string
  description: string
  value: number
  threshold: number
  unit: string
  higher_is_better: boolean
  status: BenchmarkStatus
  display_value: string
  display_threshold: string
  module_status?: string
}

export interface AuditIssue {
  line: number
  code: string
  severity: "error" | "warning"
  message: string
}

export interface AuditSummary {
  total_lines: number
  parsed_records: number
  parse_errors: number
  error_count: number
  warning_count: number
  records_with_opinions: number
  total_opinions: number
  avg_opinions_per_record: number
  train_rows?: number
  dev_rows?: number
}

export interface AuditReport {
  report_id: string
  generated_at: string
  dataset_id?: string
  dataset_key: string
  source_label: string
  schema: string
  passed: boolean
  data_level_status?: string
  summary: AuditSummary
  benchmarks: AuditBenchmark[]
  modules?: Record<string, unknown>
  distributions: {
    aspects: Record<string, number>
    opinion_sentiments: Record<string, number>
    global_sentiments: Record<string, number>
  }
  issues: AuditIssue[]
  issue_truncated?: boolean
}

export interface AuditReportListItem {
  report_id: string
  generated_at: string
  dataset_id?: string
  dataset_key: string
  source_label: string
  passed: boolean
  data_level_status?: string
  summary: AuditSummary
}

export type AuditTarget = {
  datasetId: string
}
