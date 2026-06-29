import { apiClient } from "@/lib/api/client"
import type {
  WeeklyReport,
  WeeklyReportsListResponse,
} from "@/types/weekly-report"

export async function fetchWeeklyReports(limit = 12): Promise<WeeklyReportsListResponse> {
  return apiClient<WeeklyReportsListResponse>(`/metrics/weekly-reports?limit=${limit}`)
}

export async function fetchWeeklyReport(reportId: string): Promise<WeeklyReport> {
  return apiClient<WeeklyReport>(`/metrics/weekly-reports/${encodeURIComponent(reportId)}`)
}

export async function triggerWeeklyReport(options?: {
  modelId?: string
  periodDays?: number
}): Promise<{ status: string; report: WeeklyReport }> {
  return apiClient<{ status: string; report: WeeklyReport }>("/metrics/weekly-reports", {
    method: "POST",
    body: JSON.stringify({
      model_id: options?.modelId,
      period_days: options?.periodDays ?? 7,
    }),
  })
}
