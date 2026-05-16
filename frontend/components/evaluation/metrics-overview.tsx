import type { ClassificationMetrics } from "@/types/evaluation"

type MetricsOverviewProps = {
  title: string
  metrics: ClassificationMetrics
}

export function MetricsOverview({ title, metrics }: MetricsOverviewProps) {
  const items = [
    { label: "Accuracy", value: metrics.accuracy },
    { label: "Precision", value: metrics.precision },
    { label: "Recall", value: metrics.recall },
    { label: "F1", value: metrics.f1 },
  ]

  return (
    <div>
      <h3 className="mb-3 text-sm font-medium">{title}</h3>
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {items.map((item) => (
          <div
            key={item.label}
            className="rounded-lg border border-white/[0.08] bg-white/[0.02] px-3 py-2"
          >
            <dt className="text-[10px] text-muted-foreground">{item.label}</dt>
            <dd className="mt-0.5 font-mono text-lg font-semibold tabular-nums">
              {(item.value * 100).toFixed(1)}%
            </dd>
            </div>
        ))}
      </dl>
    </div>
  )
}
