import { apiClient } from "@/lib/api/client"

export type AnalyticsSummary = {
  predictions: number
  low_confidence_rate: number
  low_confidence_threshold_pct?: number
  no_opinion_rate: number
  review_queue: number
  review_queue_pending?: number
  review_queue_urgent?: number
}

export type AnalyticsPayload = {
  summary: AnalyticsSummary
  sentiment_trend: { time: string; positive: number; neutral: number; negative: number }[]
  aspect_distribution: { aspect: string; count: number }[]
  confidence_histogram: { bin: string; count: number }[]
  drift_trend: { day: string; score: number }[]
  drift: { score: number; threshold: number; status: string }
  recent_predictions: {
    time: string
    text: string
    aspects: string[]
    sentiment: string
    confidence: number
    guardrail: "PASS" | "WARN" | "REVIEW" | "REJECT"
    model_version: string
  }[]
  models: string[]
}

export type ReviewQueueItem = {
  id: string
  time: string
  text: string
  reason: string
  model_version: string
  confidence: string
  status: string
  assigned_to: string
  guardrail: string
}

export type GuardrailThresholds = {
  reject_global: number
  review_global: number
  warn_global: number
  aspect_low: number
  aspect_warn_count: number
  aspect_review_count: number
  no_opinion_reject: number
  no_opinion_review: number
  low_confidence_analytics: number
}

export type PlatformSettings = {
  environment: string
  model_dir: string
  production_model: string
  endpoint_status: string
  artifacts_bucket: string | null
  retrain_state_machine: string | null
  pipeline_demo_mode: boolean
  drift_threshold: number
  guardrails: GuardrailThresholds
  request_volume_total: number
  uptime_seconds: number
}

export async function fetchAnalytics(
  hours = 24,
  model?: string,
): Promise<AnalyticsPayload> {
  const params = new URLSearchParams({ hours: String(hours) })
  if (model) params.set("model", model)
  return apiClient<AnalyticsPayload>(`/metrics/analytics?${params}`)
}

export async function fetchReviewQueue(limit = 50): Promise<{
  items: ReviewQueueItem[]
  open_count: number
}> {
  return apiClient(`/metrics/review-queue?limit=${limit}`)
}

export async function fetchPlatformSettings(): Promise<PlatformSettings> {
  return apiClient<PlatformSettings>("/metrics/platform")
}
