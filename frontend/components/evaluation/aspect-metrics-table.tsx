import type { AspectMetrics } from "@/types/evaluation"

type AspectMetricsTableProps = {
  aspects: AspectMetrics[]
}

export function AspectMetricsTable({ aspects }: AspectMetricsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-white/[0.08] text-left text-muted-foreground">
            <th className="pb-2 pr-4 font-medium">Aspect</th>
            <th className="pb-2 pr-4 font-medium">Span F1</th>
            <th className="pb-2 font-medium">Sentiment F1</th>
          </tr>
        </thead>
        <tbody>
          {aspects.map((a) => (
            <tr key={a.aspect} className="border-b border-white/[0.04]">
              <td className="py-2 pr-4 font-medium">{a.label}</td>
              <td className="py-2 pr-4 font-mono tabular-nums">
                {(a.recall * 100).toFixed(1)}%
              </td>
              <td className="py-2 font-mono tabular-nums">
                {(a.f1 * 100).toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
