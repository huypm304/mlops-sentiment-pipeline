import { apiClient } from "@/lib/api/client"

export type RuntimeMetrics = {
  endpoint_health: "healthy" | "degraded"
  api_status: string
  uptime_seconds: number
  request_volume_total: number
  error_count: number
  error_rate_pct: number
  avg_latency_ms: number
  p95_latency_ms: number
  recent_latency_ms: number[]
}

export type HealthResponse = RuntimeMetrics & {
  status: string
  model: string
}

export async function fetchHealth(): Promise<HealthResponse> {
  return apiClient<HealthResponse>("/health")
}

export async function fetchRuntimeMetrics(): Promise<RuntimeMetrics> {
  return apiClient<RuntimeMetrics>("/metrics/runtime")
}
