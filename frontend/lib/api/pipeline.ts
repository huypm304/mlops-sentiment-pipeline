import { apiClient } from "@/lib/api/client"
import type { ApprovalRecord, PipelineConfig, PipelineRun, TrainingConfig } from "@/types/pipeline"

export async function fetchPipelineConfig(): Promise<PipelineConfig> {
  return apiClient<PipelineConfig>("/pipeline/config")
}

export async function fetchDefaultTrainingConfig(): Promise<{ training_config: TrainingConfig }> {
  return apiClient<{ training_config: TrainingConfig }>("/pipeline/training-config")
}

export async function fetchPipelineRuns(limit = 15): Promise<{ runs: PipelineRun[] }> {
  return apiClient<{ runs: PipelineRun[] }>(`/pipeline/runs?limit=${limit}`)
}

export async function fetchPipelineRun(executionArn: string): Promise<PipelineRun> {
  return apiClient<PipelineRun>(`/pipeline/runs/${encodeURIComponent(executionArn)}`)
}

export async function triggerPipeline(body: {
  dataset_id: string
  requested_by?: string
  base_model_id?: string
  training_config?: TrainingConfig
}): Promise<PipelineRun> {
  return apiClient<PipelineRun>("/pipeline/trigger", {
    method: "POST",
    body: JSON.stringify({
      dataset_id: body.dataset_id,
      requested_by: body.requested_by ?? "admin-ui",
      base_model_id: body.base_model_id ?? "absa-v1",
      training_config: body.training_config,
    }),
  })
}

export async function fetchApproval(approvalId: string): Promise<ApprovalRecord> {
  return apiClient<ApprovalRecord>(`/pipeline/approvals/${encodeURIComponent(approvalId)}`)
}

export async function decideApproval(
  approvalId: string,
  decision: "approve" | "reject"
): Promise<{ approval_id: string; status: string }> {
  return apiClient(`/pipeline/approvals/${encodeURIComponent(approvalId)}/decide`, {
    method: "POST",
    body: JSON.stringify({ decision, decided_by: "admin-ui" }),
  })
}
