"use client"

import { ModelDetail } from "@/components/admin/model-detail"

type Props = {
  version: string
}

export function ModelDetailPageClient({ version }: Props) {
  return <ModelDetail version={version} />
}
