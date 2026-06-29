import type { AuditBenchmark, AuditIssue } from "@/types/audit"

export type DatasetSplit = "train" | "dev" | "test" | "bundle"
export type DatasetStatus = "pending" | "audited" | "approved" | "failed"

export type SplitFileInfo = {
  filename: string
  rows: number
  size_bytes: number
}

export type SplitAuditInfo = {
  report_id: string
  passed: boolean
  audit_score: number
  error_count: number
  generated_at: string
  data_level_status?: string
  failed_checks?: string[]
  benchmarks?: AuditBenchmark[]
  distributions?: {
    aspects?: Record<string, number>
    opinion_sentiments?: Record<string, number>
    global_sentiments?: Record<string, number>
  }
  issues?: AuditIssue[]
  issue_truncated?: boolean
  summary?: {
    train_rows?: number
    dev_rows?: number
    warning_count?: number
    parsed_records?: number
    total_opinions?: number
    avg_opinions_per_record?: number
  }
}

export type DatasetManifest = {
  dataset_id: string
  name: string
  status: DatasetStatus
  created_at: string
  updated_at: string
  splits: Record<string, SplitFileInfo>
  audits: Record<string, SplitAuditInfo>
  audit_passed: boolean
}

export type DatasetListItem = {
  dataset_id: string
  name: string
  status: DatasetStatus
  created_at: string
  splits: string[]
  audit_passed: boolean
  audit_status?: "pass" | "pending" | "running" | "fail"
  audit_score: number | null
  total_rows: number
}

export type SplitAuditResult = {
  split: DatasetSplit
  report_id: string
  passed: boolean
  audit_score: number
  summary: Record<string, number>
}

export type DatasetAuditResponse = {
  dataset_id: string
  passed: boolean
  report_id: string
  report_key?: string
  data_level_status?: string
  audit_score?: number
  summary?: Record<string, number>
  benchmarks?: AuditBenchmark[]
  distributions?: SplitAuditInfo["distributions"]
  issues?: AuditIssue[]
  issue_truncated?: boolean
  results?: SplitAuditResult[]
}
