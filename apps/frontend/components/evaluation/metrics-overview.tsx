import type { ClassificationMetrics } from "@/types/evaluation"

type MetricsOverviewProps = {
  title: string
  metrics: ClassificationMetrics
  /** Decimal places for percentage display (default 2). */
  decimals?: number
  /** Hide accuracy when the task only reports span-level P/R/F1. */
  showAccuracy?: boolean
}

export function MetricsOverview({
  title,
  metrics,
  decimals = 2,
  showAccuracy = true,
}: MetricsOverviewProps) {
  const items = [
    ...(showAccuracy && metrics.accuracy != null
      ? [{ label: "Accuracy", value: metrics.accuracy }]
      : []),
    { label: "Precision", value: metrics.precision },
    { label: "Recall", value: metrics.recall },
    { label: "F1", value: metrics.f1 },
  ]

  return (
    <div>
      <h3 className="mb-3 text-sm font-medium">{title}</h3>
      <dl className={`grid gap-3 ${items.length === 3 ? "grid-cols-3" : "grid-cols-2 sm:grid-cols-4"}`}>
        {items.map((item) => (
          <div
            key={item.label}
            className="rounded-lg border border-white/[0.08] bg-white/[0.02] px-3 py-2"
          >
            <dt className="text-[10px] text-muted-foreground">{item.label}</dt>
            <dd className="mt-0.5 font-mono text-lg font-semibold tabular-nums">
              {(item.value * 100).toFixed(decimals)}%
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
