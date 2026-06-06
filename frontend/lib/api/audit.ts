import { apiClient } from "@/lib/api/client"
import type { AuditReport, AuditReportListItem } from "@/types/audit"

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
  dataset: "train" | "demo" = "train"
): Promise<{ report_id: string; passed: boolean }> {
  return apiClient("/audit/run", {
    method: "POST",
    body: JSON.stringify({ dataset }),
  })
}
