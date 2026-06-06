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

export type DriftComparisonRow = {
  name: string
  baseline: number
  production: number
  delta: number
}

export type DriftReport = {
  status: "ok" | "warning" | "alert" | "insufficient_data"
  message: string
  production_sample_size: number
  drift_score: number
  aspect_drift: number
  sentiment_drift: number
  confidence_delta: number
  threshold: number
  suggest_retrain: boolean
  signals: string[]
  comparison: DriftComparisonRow[]
  baseline: {
    sample_size: number
    aspect_distribution: Record<string, number>
    global_sentiment_distribution: Record<string, number>
  }
  production: {
    sample_size: number
    aspect_distribution: Record<string, number>
    global_sentiment_distribution: Record<string, number>
    avg_global_confidence: number
  }
}

export type MonitoringPayload = RuntimeMetrics & {
  drift: DriftReport
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

export async function fetchMonitoring(): Promise<MonitoringPayload> {
  return apiClient<MonitoringPayload>("/metrics/monitoring")
}
