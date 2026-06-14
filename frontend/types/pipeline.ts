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
  sagemaker_instance_type?: string
}

export type RunComparison = {
  production_baseline: Record<string, number>
  candidate_metrics: Record<string, number>
  delta: Record<string, number>
  metric_gate_passed: boolean
  promote?: boolean
}

export type RunEvaluation = {
  run_id: string
  candidate_model_id?: string
  metrics: Record<string, number>
  evaluated_at?: string
  mode?: string
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
  run_id?: string
  base_model_id?: string
  candidate_model_id?: string
  best_f1?: number | null
  duration_seconds?: number | null
  artifact_uri?: string | null
  approval_id?: string
  training_config?: TrainingConfig
  demo?: boolean
  current_stage?: string | null
  current_state?: string | null
  message?: string
  stages: PipelineStage[]
  sfn_steps?: SfnStep[]
  evaluation?: RunEvaluation
  comparison?: RunComparison
}

export type PipelineConfig = {
  configured: boolean
  demo_mode: boolean
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
