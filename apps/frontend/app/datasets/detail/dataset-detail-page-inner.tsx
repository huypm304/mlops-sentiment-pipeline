"use client"

import { Loader2 } from "lucide-react"
import { useSearchParams } from "next/navigation"

import { DatasetDetailClient } from "../[datasetId]/dataset-detail-client"

export function DatasetDetailPageInner() {
  const params = useSearchParams()
  const datasetId = params.get("id")?.trim() ?? ""

  if (!datasetId) {
    return (
      <p className="py-8 text-sm text-muted-foreground">
        Missing dataset id. Open a dataset from the registry list.
      </p>
    )
  }

  return <DatasetDetailClient datasetId={datasetId} />
}

export function DatasetDetailPageFallback() {
  return (
    <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
      <Loader2 className="size-4 animate-spin" />
      Loading dataset detail
    </div>
  )
}
