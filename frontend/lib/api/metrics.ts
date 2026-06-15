import { apiClient } from "@/lib/api/client"
import type {
  EvaluationScores,
  ModelSummary,
  TrainingHistoryPoint,
} from "@/lib/constants/metrics"
import type { ModelEvaluation } from "@/types/evaluation"

type MetricsApiEvaluation = {
  version: string
  status: "production" | "archived"
  epoch: number
  phase: string
  primary_metric: string
  registered_at: string
  evaluated_at: string
  inference_latency_ms: number
  dataset: {
    version: string
    train_samples: number
    val_samples: number
    test_samples: number
  }
  training: {
    encoder: string
    epochs: number
    batch_size: number
    learning_rate: number
    trained_at: string
    checkpoint: string
  }
  scores: EvaluationScores
  sentiment: {
    accuracy: number
    precision: number
    recall: number
    f1: number
  }
  global_sentiment: {
    accuracy: number
    precision: number
    recall: number
    f1: number
  }
  aspect_polarity: {
    accuracy: number
    precision: number
    recall: number
    f1: number
  }
  aspect_extraction: {
    accuracy: number
    precision: number
    recall: number
    f1: number
  }
  confusion_matrix: {
    labels: ["negative", "neutral", "positive"]
    matrix: [number[], number[], number[]]
  }
  per_aspect: {
    aspect: string
    label: string
    span_f1: number
    sent_f1: number
    f1: number
    precision: number
    recall: number
    support: number
  }[]
}

export type { EvaluationScores, ModelSummary, TrainingHistoryPoint }

function mapEvaluation(data: MetricsApiEvaluation): ModelEvaluation {
  return {
    version: data.version,
    status: data.status,
    registeredAt: data.registered_at,
    evaluatedAt: data.evaluated_at,
    inferenceLatencyMs: data.inference_latency_ms,
    primaryMetric: data.primary_metric,
    dataset: {
      version: data.dataset.version,
      trainSamples: data.dataset.train_samples,
      valSamples: data.dataset.val_samples,
      testSamples: data.dataset.test_samples,
    },
    training: {
      encoder: data.training.encoder,
      epochs: data.training.epochs,
      batchSize: data.training.batch_size,
      learningRate: data.training.learning_rate,
      trainedAt: data.training.trained_at,
      checkpoint: data.training.checkpoint,
    },
    sentiment: data.sentiment,
    globalSentiment: data.global_sentiment,
    aspectPolarity: data.aspect_polarity,
    aspectExtraction: data.aspect_extraction,
    confusionMatrix: data.confusion_matrix,
    perAspect: data.per_aspect.map((a) => ({
      aspect: a.aspect,
      label: a.label,
      precision: a.precision,
      recall: a.recall,
      f1: a.f1,
      support: a.support,
    })),
    epoch: data.epoch,
    phase: data.phase,
    scores: data.scores,
  }
}

export async function fetchModels(): Promise<ModelSummary[]> {
  const res = await apiClient<{ models: ModelSummary[] }>("/metrics/models")
  return res.models
}

export async function fetchModelEvaluation(
  version: string
): Promise<ModelEvaluation> {
  const data = await apiClient<MetricsApiEvaluation>(
    `/metrics/models/${encodeURIComponent(version)}`
  )
  return mapEvaluation(data)
}

export async function fetchTrainingHistory(): Promise<TrainingHistoryPoint[]> {
  const res = await apiClient<{ history: TrainingHistoryPoint[] }>(
    "/metrics/training/history"
  )
  return res.history
}
