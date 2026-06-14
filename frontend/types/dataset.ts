export type DatasetSplit = "train" | "dev" | "test" | "bundle"
export type DatasetStatus = "pending" | "audited" | "approved"

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
  results: SplitAuditResult[]
}
