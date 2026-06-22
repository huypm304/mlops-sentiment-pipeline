"use client"

import { useEffect, useState } from "react"
import { Inbox, Loader2 } from "lucide-react"

import { EmptyState } from "@/components/ui/empty-state"
import { fetchReviewQueue, type ReviewQueueItem } from "@/lib/api/analytics"
import { cn } from "@/lib/utils"

const STATUS_STYLES: Record<string, string> = {
  Pending: "bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20",
  "In review": "bg-blue-500/10 text-blue-400 ring-1 ring-blue-500/20",
  Resolved: "bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20",
}

const GUARDRAIL_STYLES: Record<string, string> = {
  WARN: "text-amber-400",
  REVIEW: "text-blue-400",
  REJECT: "text-red-400",
}

export default function ReviewQueuePage() {
  const [items, setItems] = useState<ReviewQueueItem[]>([])
  const [openCount, setOpenCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchReviewQueue()
      .then((res) => {
        setItems(res.items)
        setOpenCount(res.open_count)
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load review queue"),
      )
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading review queue…
      </div>
    )
  }

  if (error) {
    return <EmptyState title="Review queue unavailable" description={error} />
  }

  return (
    <div className="space-y-4">
      <header className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-[15px] font-semibold tracking-tight">Review Queue</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Low-confidence and flagged predictions from inference log
          </p>
        </div>
        {openCount > 0 && (
          <span className="rounded bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-400">
            {openCount} open
          </span>
        )}
      </header>

      <div className="rounded-lg border border-border/60 bg-card">
        {items.length === 0 ? (
          <div className="flex flex-col items-center py-12 text-center">
            <Inbox className="mb-3 size-8 text-muted-foreground/30" />
            <p className="text-sm text-muted-foreground">Queue is empty</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Flagged predictions appear here after inference runs
            </p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border/40 text-[11px] text-muted-foreground">
                <th className="px-4 py-2.5 text-left font-medium">Time</th>
                <th className="px-4 py-2.5 text-left font-medium">Text preview</th>
                <th className="px-4 py-2.5 text-left font-medium">Reason</th>
                <th className="px-4 py-2.5 text-left font-medium">Model</th>
                <th className="px-4 py-2.5 text-left font-medium">Confidence</th>
                <th className="px-4 py-2.5 text-left font-medium">Guardrail</th>
                <th className="px-4 py-2.5 text-left font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr
                  key={row.id}
                  className="border-b border-border/30 last:border-0 hover:bg-muted/30 transition-colors"
                >
                  <td className="px-4 py-2.5 font-mono text-[11px] text-muted-foreground whitespace-nowrap">
                    {row.time}
                  </td>
                  <td className="px-4 py-2.5 max-w-[260px] truncate text-[13px]">{row.text}</td>
                  <td className="px-4 py-2.5 text-[12px] text-muted-foreground">{row.reason}</td>
                  <td className="px-4 py-2.5 font-mono text-[12px]">{row.model_version}</td>
                  <td className="px-4 py-2.5 font-mono text-[12px] tabular-nums">{row.confidence}</td>
                  <td className={cn("px-4 py-2.5 text-[11px] font-medium", GUARDRAIL_STYLES[row.guardrail])}>
                    {row.guardrail}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={cn("rounded px-1.5 py-0.5 text-[10px] font-medium", STATUS_STYLES[row.status] ?? "")}>
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
