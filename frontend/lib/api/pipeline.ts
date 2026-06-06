import { apiClient } from "@/lib/api/client"
import type { PipelineConfig, PipelineRun } from "@/types/pipeline"

export async function fetchPipelineConfig(): Promise<PipelineConfig> {
  return apiClient<PipelineConfig>("/pipeline/config")
}

export async function fetchPipelineRuns(limit = 15): Promise<{ runs: PipelineRun[] }> {
  return apiClient<{ runs: PipelineRun[] }>(`/pipeline/runs?limit=${limit}`)
}

export async function triggerPipeline(body?: {
  dataset_key?: string
  requested_by?: string
}): Promise<PipelineRun> {
  return apiClient<PipelineRun>("/pipeline/trigger", {
    method: "POST",
    body: JSON.stringify({
      dataset_key: body?.dataset_key ?? "datasets/raw/latest.jsonl",
      requested_by: body?.requested_by ?? "admin-ui",
    }),
  })
}
