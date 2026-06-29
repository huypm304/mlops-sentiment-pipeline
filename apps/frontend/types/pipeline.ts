export type PipelineStageStatus = "completed" | "running" | "failed" | "pending"

export type PipelineStage = {
  name: string
  status: PipelineStageStatus
}

export type TrainingConfig = {
  model_name?: string
  epochs?: number
  patience?: number
  batch_size?: number
  lr_backbone?: number
  lr_heads?: number
  lambda_bio?: number
  lambda_sent?: number
  lambda_global?: number
  lambda_cons?: number
  lambda_contrast?: number
  contrast_sampler_weight?: number
  pred_span_ratio?: number
  sagemaker_instance_type?: string
}

export type RunComparison = {
  production_baseline: Record<string, number>
  candidate_metrics: Record<string, number>
  delta: Record<string, number>
  metric_gate_passed: boolean
  promote?: boolean
  baseline_model_id?: string
  candidate_model_id?: string
  primary_metric?: string
}

export type RunEvaluation = {
  run_id: string
  candidate_model_id?: string
  metrics: Record<string, number>
  evaluated_at?: string
  mode?: string
  best_f1?: number
  passed?: boolean
}

export type SfnStep = {
  id: string
  name: string
  status: PipelineStageStatus
}

export type PipelineRun = {
  execution_arn: string
  name: string
  status: string
  start_date: string
  stop_date: string | null
  dataset_key: string | null
  dataset_id?: string
  dataset_s3_uri?: string | null
  run_id?: string
  base_model_id?: string
  candidate_model_id?: string
  code_version?: string | null
  training_source_uri?: string | null
  best_f1?: number | null
  duration_seconds?: number | null
  artifact_uri?: string | null
  production_uri?: string | null
  approval_id?: string
  training_config?: TrainingConfig
  metrics?: Record<string, number>
  demo?: boolean
  current_stage?: string | null
  current_state?: string | null
  sfn_status?: string | null
  message?: string
  stages: PipelineStage[]
  sfn_steps?: SfnStep[]
  evaluation?: RunEvaluation
  comparison?: RunComparison
}

export type PipelineConfig = {
  configured: boolean
  demo_mode: boolean
  sagemaker_training_enabled?: boolean
  training_mode?: "sagemaker" | "mock"
  state_machine_arn: string | null
  artifacts_bucket: string | null
  stages: string[]
  default_training_config?: TrainingConfig
  message: string
}

export type ApprovalRecord = {
  approval_id: string
  run_id: string
  status: string
  dataset_id?: string
  dataset_key?: string
  training_config?: TrainingConfig
  cost_estimate?: { estimated_usd?: number; mode?: string }
}

/** Defaults aligned with apps/backend/lambda/pipeline/default_training_config.json and train_kaggle.py */
export const DEFAULT_TRAINING_CONFIG: TrainingConfig = {
  epochs: 50,
  patience: 8,
  batch_size: 24,
  lr_backbone: 8e-6,
  lr_heads: 3e-5,
  lambda_bio: 1.1,
  lambda_sent: 1.4,
  lambda_global: 0.2,
  lambda_cons: 0.03,
  lambda_contrast: 0.1,
  contrast_sampler_weight: 1.2,
  pred_span_ratio: 0.1,
}

/** Editable hyperparameter fields exposed in console/admin trigger forms. */
export const TRAINING_CONFIG_FIELDS = [
  "epochs",
  "patience",
  "batch_size",
  "lr_backbone",
  "lr_heads",
  "lambda_bio",
  "lambda_sent",
  "lambda_global",
  "lambda_cons",
  "lambda_contrast",
  "contrast_sampler_weight",
  "pred_span_ratio",
] as const

export type TrainingConfigField = (typeof TRAINING_CONFIG_FIELDS)[number]
