"use client"

import { Loader2 } from "lucide-react"
import { useSearchParams } from "next/navigation"

import { RunDetailClient } from "../[runId]/run-detail-client"

export function TrainingRunDetailPageInner() {
  const params = useSearchParams()
  const runId = params.get("id")?.trim() ?? ""

  if (!runId) {
    return (
      <p className="py-8 text-sm text-muted-foreground">
        Missing run id. Open a run from the Training Runs list.
      </p>
    )
  }

  return <RunDetailClient runId={runId} />
}

export function TrainingRunDetailPageFallback() {
  return (
    <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
      <Loader2 className="size-4 animate-spin" />
      Loading run detail
    </div>
  )
}
