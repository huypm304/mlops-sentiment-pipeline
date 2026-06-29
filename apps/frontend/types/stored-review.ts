import type { InferenceResult } from "@/types/dashboard"

export type StoredReview = {
  id: string
  text: string
  date: string
  globalSentiment: InferenceResult["globalSentiment"]
  result: InferenceResult
}
