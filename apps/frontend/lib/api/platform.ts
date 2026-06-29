import { apiClient } from "@/lib/api/client"

export type PlatformContext = {
  environment: string
  champion_model: string | null
  active_dataset: string | null
  active_dataset_name: string | null
  api_status: string
  last_training_at: string | null
  pipeline_demo_mode: boolean
}

export async function fetchPlatformContext(): Promise<PlatformContext> {
  return apiClient<PlatformContext>("/metrics/platform/context")
}
