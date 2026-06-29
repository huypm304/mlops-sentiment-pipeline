import { apiClient } from "@/lib/api/client"
import type { AuditReport, AuditReportListItem, AuditTarget } from "@/types/audit"
import type { DatasetListItem } from "@/types/dataset"

export type { AuditTarget }

export async function fetchAuditReports(): Promise<AuditReportListItem[]> {
  const data = await apiClient<{ reports: AuditReportListItem[] }>("/audit/reports")
  return data.reports
}

export async function fetchLatestAuditReport(): Promise<AuditReport> {
  return apiClient<AuditReport>("/audit/reports/latest")
}

export async function fetchAuditReport(reportId: string): Promise<AuditReport> {
  return apiClient<AuditReport>(`/audit/reports/${reportId}`)
}

export async function runDatasetAudit(
  target: AuditTarget,
): Promise<{ report_id: string; passed: boolean; data_level_status?: string }> {
  return apiClient("/audit/run", {
    method: "POST",
    body: JSON.stringify({ dataset_id: target.datasetId }),
  })
}

export function formatAuditTargetLabel(
  target: AuditTarget,
  datasets: DatasetListItem[],
): string {
  const dataset = datasets.find((d) => d.dataset_id === target.datasetId)
  const name = dataset?.name ?? target.datasetId
  return `${name} · train+dev`
}

export function defaultAuditTarget(datasets: DatasetListItem[]): AuditTarget | null {
  if (datasets.length === 0) return null
  return { datasetId: datasets[0].dataset_id }
}
