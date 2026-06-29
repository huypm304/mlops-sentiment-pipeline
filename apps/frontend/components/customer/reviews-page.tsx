"use client"

import { useState } from "react"

import { ReviewAnalyzer } from "@/components/customer/review-analyzer"
import { ReviewInbox } from "@/components/customer/review-inbox"
import type { StoredReview } from "@/types/stored-review"

export function ReviewsPage() {
  const [history, setHistory] = useState<StoredReview[]>([])

  function handleAnalyzed(
    result: StoredReview["result"],
    text: string
  ) {
    setHistory((prev) => [
      {
        id: crypto.randomUUID(),
        text,
        date: new Date().toISOString().slice(0, 10),
        globalSentiment: result.globalSentiment,
        result,
      },
      ...prev,
    ])
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-xl font-semibold tracking-tight">Reviews</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Analyze new feedback and browse past results
        </p>
      </header>

      <section>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">
          New analysis
        </h2>
        <ReviewAnalyzer onAnalyzed={handleAnalyzed} />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">
          Review history
        </h2>
        <ReviewInbox reviews={history} />
      </section>
    </div>
  )
}
