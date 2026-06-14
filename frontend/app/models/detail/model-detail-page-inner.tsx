"use client"

import { Loader2 } from "lucide-react"
import { useSearchParams } from "next/navigation"

import { ModelDetailClient } from "../[version]/model-detail-client"

export function ModelDetailPageInner() {
  const params = useSearchParams()
  const version = params.get("version")?.trim() ?? ""

  if (!version) {
    return (
      <p className="py-8 text-sm text-muted-foreground">
        Missing model version. Open a model from the registry list.
      </p>
    )
  }

  return <ModelDetailClient version={version} />
}

export function ModelDetailPageFallback() {
  return (
    <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
      <Loader2 className="size-4 animate-spin" />
      Loading model detail
    </div>
  )
}
