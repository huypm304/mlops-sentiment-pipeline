import type { InferenceResult } from "@/types/dashboard"

export type GuardrailStatus = "PASS" | "WARN" | "REVIEW" | "REJECT"

/** Keep in sync with backend/app/config/guardrails.py */
export const GUARDRAIL_THRESHOLDS = {
  reject_global: 0.18,
  review_global: 0.25,
  warn_global: 0.32,
  aspect_low: 0.22,
  aspect_warn_count: 2,
  aspect_review_count: 3,
  no_opinion_reject: 0.22,
  no_opinion_review: 0.3,
  low_confidence_analytics: 0.32,
} as const

function pct(value: number): string {
  return `${Math.round(value * 100)}%`
}

export function evaluateGuardrail(result: {
  globalConfidence: number
  aspects: InferenceResult["aspects"]
}): { status: GuardrailStatus; reasons: string[] } {
  const cfg = GUARDRAIL_THRESHOLDS
  const c = result.globalConfidence
  const aspects = result.aspects

  const lowAspects = aspects.filter(
    (a) => (a.calibratedConfidence ?? a.confidence) < cfg.aspect_low,
  )

  let status: GuardrailStatus = "PASS"
  const reasons: string[] = []

  if (
    c < cfg.reject_global ||
    (aspects.length === 0 && c < cfg.no_opinion_reject)
  ) {
    status = "REJECT"
    if (c < cfg.reject_global) {
      reasons.push(
        `Global confidence below ${pct(cfg.reject_global)} — prediction unreliable`,
      )
    }
    if (aspects.length === 0) {
      reasons.push("No aspect opinions extracted (no-opinion output)")
      if (c < cfg.no_opinion_reject) {
        reasons.push(
          `No-opinion output with global confidence below ${pct(cfg.no_opinion_reject)}`,
        )
      }
    }
  } else if (
    c < cfg.review_global ||
    (aspects.length === 0 && c < cfg.no_opinion_review) ||
    lowAspects.length >= cfg.aspect_review_count
  ) {
    status = "REVIEW"
    if (c < cfg.review_global) {
      reasons.push(
        `Global confidence below ${pct(cfg.review_global)} — recommend human review`,
      )
    }
    if (aspects.length === 0) {
      reasons.push("No aspect opinions extracted (no-opinion output)")
    }
    if (lowAspects.length >= cfg.aspect_review_count) {
      reasons.push(
        `${lowAspects.length} aspect(s) below ${pct(cfg.aspect_low)} confidence: ${lowAspects.map((a) => a.aspect).join(", ")}`,
      )
    }
  } else if (c < cfg.warn_global || lowAspects.length >= cfg.aspect_warn_count) {
    status = "WARN"
    if (c < cfg.warn_global) {
      reasons.push(
        `Global confidence below ${pct(cfg.warn_global)} — soft low-confidence flag`,
      )
    }
    if (lowAspects.length >= cfg.aspect_warn_count) {
      reasons.push(
        `${lowAspects.length} aspect(s) below ${pct(cfg.aspect_low)} confidence: ${lowAspects.map((a) => a.aspect).join(", ")}`,
      )
    }
  } else if (aspects.length === 0) {
    reasons.push("No aspect opinions extracted (informational only)")
  }

  if (status === "PASS" && reasons.length === 0) {
    reasons.push("Prediction meets confidence thresholds")
  }

  return { status, reasons }
}
