import { Suspense } from "react"

import {
  ModelDetailPageFallback,
  ModelDetailPageInner,
} from "./model-detail-page-inner"

export default function ModelDetailQueryPage() {
  return (
    <Suspense fallback={<ModelDetailPageFallback />}>
      <ModelDetailPageInner />
    </Suspense>
  )
}
