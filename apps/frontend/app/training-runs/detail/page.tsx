import { Suspense } from "react"

import {
  TrainingRunDetailPageFallback,
  TrainingRunDetailPageInner,
} from "./training-run-detail-page-inner"

export default function TrainingRunDetailQueryPage() {
  return (
    <Suspense fallback={<TrainingRunDetailPageFallback />}>
      <TrainingRunDetailPageInner />
    </Suspense>
  )
}
