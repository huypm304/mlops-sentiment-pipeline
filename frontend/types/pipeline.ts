export type PipelineStageStatus = "completed" | "running" | "failed" | "pending"

export type PipelineStage = {
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
  demo?: boolean
  current_stage?: string | null
  message?: string
  stages: PipelineStage[]
}

export type PipelineConfig = {
  configured: boolean
  demo_mode: boolean
  state_machine_arn: string | null
  artifacts_bucket: string | null
  stages: string[]
  message: string
}
