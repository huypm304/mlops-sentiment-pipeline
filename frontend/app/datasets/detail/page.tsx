import { Suspense } from "react"

import {
  DatasetDetailPageFallback,
  DatasetDetailPageInner,
} from "./dataset-detail-page-inner"

export default function DatasetDetailQueryPage() {
  return (
    <Suspense fallback={<DatasetDetailPageFallback />}>
      <DatasetDetailPageInner />
    </Suspense>
  )
}
