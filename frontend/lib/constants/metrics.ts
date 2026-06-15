export const PRIMARY_METRIC = "tas_relaxed_f1" as const

export const METRIC_LABELS: Record<string, string> = {
  tas_strict_f1: "TAS Strict F1",
  tas_relaxed_f1: "TAS Relaxed F1",
  span_f1: "Span F1",
  sent_matched_f1: "Sent@Matched F1",
  sent_goldspan_f1: "Sent@GoldSpan F1",
  global_f1: "Global F1",
  train_loss: "Train loss",
}

export type EvaluationScores = {
  tas_strict_f1: number
  tas_relaxed_f1: number
  span_f1: number
  sent_matched_f1: number
  sent_goldspan_f1: number
  global_f1: number
  train_loss: number
}

export type TrainingHistoryPoint = {
  epoch: number
  phase: string
  is_best: boolean
} & EvaluationScores

export type ModelSummary = {
  version: string
  status: string
  epoch: number
  primary_metric: typeof PRIMARY_METRIC
  tas_strict_f1: number
  tas_relaxed_f1: number
  span_f1: number
  sent_matched_f1: number
  sent_goldspan_f1: number
  global_f1: number
  encoder: string
  checkpoint: string
}

export function metricLabel(key: keyof EvaluationScores | string): string {
  return METRIC_LABELS[key] ?? key
}

export function hasEvaluationScores(scores: Partial<EvaluationScores> | undefined): boolean {
  return Boolean(scores && scores.tas_relaxed_f1 && scores.tas_relaxed_f1 > 0)
}
