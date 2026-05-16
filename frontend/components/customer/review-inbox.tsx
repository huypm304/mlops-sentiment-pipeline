"use client"

import { useMemo, useState } from "react"

import { HighlightedText } from "@/components/customer/highlighted-text"
import { EmptyState } from "@/components/ui/empty-state"
import { cn } from "@/lib/utils"
import type { StoredReview } from "@/types/stored-review"

type SortKey = "date" | "sentiment"
type FilterSentiment = "all" | "positive" | "negative" | "neutral"

type ReviewInboxProps = {
  reviews: StoredReview[]
}

export function ReviewInbox({ reviews }: ReviewInboxProps) {
  const [filter, setFilter] = useState<FilterSentiment>("all")
  const [sort, setSort] = useState<SortKey>("date")
  const [selectedId, setSelectedId] = useState<string | undefined>()

  const filtered = useMemo(() => {
    let list = [...reviews]
    if (filter !== "all") {
      list = list.filter((r) => r.globalSentiment === filter)
    }
    list.sort((a, b) => {
      if (sort === "date") return b.date.localeCompare(a.date)
      return a.globalSentiment.localeCompare(b.globalSentiment)
    })
    return list
  }, [reviews, filter, sort])

  const selected =
    filtered.find((r) => r.id === selectedId) ?? filtered[0] ?? null

  if (reviews.length === 0) {
    return (
      <EmptyState
        title="No reviews yet"
        description="Run an analysis above — results will appear here for this session."
      />
    )
  }

  return (
    <div className="flex flex-col gap-3 lg:flex-row">
      <div className="w-full shrink-0 lg:w-72">
        <div className="mb-2 flex flex-wrap gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as FilterSentiment)}
            className="h-8 rounded-md border border-white/[0.08] bg-background px-2 text-xs"
          >
            <option value="all">All sentiment</option>
            <option value="positive">Positive</option>
            <option value="negative">Negative</option>
            <option value="neutral">Neutral</option>
          </select>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
            className="h-8 rounded-md border border-white/[0.08] bg-background px-2 text-xs"
          >
            <option value="date">Newest first</option>
            <option value="sentiment">By sentiment</option>
          </select>
        </div>
        <ul className="max-h-[420px] space-y-1 overflow-y-auto rounded-lg border border-white/[0.08] p-1">
          {filtered.map((r) => (
            <li key={r.id}>
              <button
                type="button"
                onClick={() => setSelectedId(r.id)}
                className={cn(
                  "w-full rounded-md px-3 py-2 text-left text-xs transition-colors",
                  selected?.id === r.id
                    ? "bg-primary/10 text-foreground"
                    : "hover:bg-white/[0.04]"
                )}
              >
                <p className="line-clamp-2 text-foreground">{r.text}</p>
                <p className="mt-1 flex justify-between text-muted-foreground">
                  <span>{r.date}</span>
                  <span className="capitalize">{r.globalSentiment}</span>
                </p>
              </button>
            </li>
          ))}
        </ul>
      </div>
      {selected ? <ReviewDetail review={selected} /> : null}
    </div>
  )
}

function ReviewDetail({ review }: { review: StoredReview }) {
  return (
    <div className="min-w-0 flex-1 rounded-lg border border-white/[0.08] bg-white/[0.02] p-4">
      <p className="text-xs text-muted-foreground">{review.date}</p>
      <HighlightedText
        text={review.text}
        spans={review.result.spans}
        className="mt-3"
      />
    </div>
  )
}
