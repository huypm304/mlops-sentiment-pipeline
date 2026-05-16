export type ClassificationMetrics = {
  accuracy: number
  precision: number
  recall: number
  f1: number
}

export type AspectMetrics = {
  aspect: string
  label: string
  precision: number
  recall: number
  f1: number
  support: number
}

export type ConfusionMatrix = {
  labels: ["negative", "neutral", "positive"]
  /** rows = actual, cols = predicted */
  matrix: [number[], number[], number[]]
}

export type ModelEvaluation = {
  version: string
  status: "production" | "archived"
  registeredAt: string
  evaluatedAt: string
  inferenceLatencyMs: number
  epoch?: number
  phase?: string
  scores?: {
    span_f1: number
    sent_f1: number
    glob_f1: number
    composite: number
    train_loss: number
  }
  dataset: {
    version: string
    trainSamples: number
    valSamples: number
    testSamples: number
  }
  training: {
    encoder: string
    epochs: number
    batchSize: number
    learningRate: number
    trainedAt: string
    checkpoint: string
  }
  /** Span-level sentiment head */
  sentiment: ClassificationMetrics
  /** Document-level global sentiment */
  globalSentiment?: ClassificationMetrics
  /** Aspect + polarity (multi-task aggregate) */
  aspectPolarity: ClassificationMetrics
  /** BIO span F1 proxy */
  aspectExtraction: ClassificationMetrics
  confusionMatrix: ConfusionMatrix
  perAspect: AspectMetrics[]
}

export type MetricComparisonRow = {
  key: string
  label: string
  baseline: number
  candidate: number
  delta: number
  higherIsBetter: boolean
}

export type ModelComparisonReport = {
  baseline: string
  candidate: string
  generatedAt: string
  datasetVersion: string
  recommendation: "promote" | "review" | "reject"
  summary: string
  highlights: string[]
  overall: MetricComparisonRow[]
  perAspect: {
    aspect: string
    label: string
    baselineF1: number
    candidateF1: number
    delta: number
  }[]
  latency: { baseline: number; candidate: number; delta: number }
}
