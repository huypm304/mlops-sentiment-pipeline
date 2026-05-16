import { apiClient } from "@/lib/api/client"
import type { InferenceResult } from "@/types/dashboard"

export type PredictOpinion = {
  target: string
  aspect: string
  sentiment: string
  confidence: number
  start?: number | null
  end?: number | null
}

export type PredictApiResponse = {
  opinions: PredictOpinion[]
  global_sentiment: string
  global_confidence: number
  latency_ms: number
}

function toSentiment(
  value: string
): "positive" | "negative" | "neutral" {
  const s = value.toLowerCase()
  if (s === "positive") return "positive"
  if (s === "negative") return "negative"
  return "neutral"
}

export function mapPredictToInference(
  data: PredictApiResponse,
  text: string
): InferenceResult {
  const aspects = data.opinions.map((o) => ({
    aspect: o.aspect,
    target: o.target,
    sentiment: toSentiment(o.sentiment),
    confidence: o.confidence,
  }))

  const spans = data.opinions
    .map((o) => {
      const start =
        o.start != null && o.start >= 0
          ? o.start
          : text.indexOf(o.target)
      const end =
        o.end != null && o.end > start
          ? o.end
          : start >= 0
            ? start + o.target.length
            : -1
      return {
        aspect: o.aspect,
        target: o.target,
        sentiment: toSentiment(o.sentiment),
        confidence: o.confidence,
        start,
        end,
      }
    })
    .filter((s) => s.start >= 0 && s.end > s.start)

  return {
    globalSentiment: toSentiment(data.global_sentiment),
    globalConfidence: data.global_confidence,
    aspects,
    spans,
    latencyMs: data.latency_ms,
  }
}

export async function predictReview(text: string): Promise<InferenceResult> {
  const data = await apiClient<PredictApiResponse>("/predict", {
    method: "POST",
    body: JSON.stringify({ text }),
  })
  return mapPredictToInference(data, text)
}
