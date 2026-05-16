import type { ConfusionMatrix } from "@/types/evaluation"
import { cn } from "@/lib/utils"

type ConfusionMatrixViewProps = {
  title: string
  data: ConfusionMatrix
  className?: string
}

const labelDisplay = {
  negative: "Neg",
  neutral: "Neu",
  positive: "Pos",
} as const

export function ConfusionMatrixView({
  title,
  data,
  className,
}: ConfusionMatrixViewProps) {
  const maxVal = Math.max(...data.matrix.flat(), 1)

  return (
    <div className={cn("space-y-2", className)}>
      <h3 className="text-sm font-medium">{title}</h3>
      <p className="text-[10px] text-muted-foreground">
        Rows: actual · Columns: predicted
      </p>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[240px] border-collapse text-xs">
          <thead>
            <tr>
              <th className="p-1 text-left text-muted-foreground" />
              {data.labels.map((l) => (
                <th key={l} className="p-1 font-medium capitalize">
                  {labelDisplay[l]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.matrix.map((row, ri) => (
              <tr key={data.labels[ri]}>
                <th className="p-1 text-left font-medium capitalize text-muted-foreground">
                  {labelDisplay[data.labels[ri]]}
                </th>
                {row.map((cell, ci) => (
                  <td key={ci} className="p-1">
                    <div
                      className="flex h-8 min-w-[2.5rem] items-center justify-center rounded font-mono tabular-nums"
                      style={{
                        backgroundColor: `color-mix(in oklab, var(--chart-1) ${(cell / maxVal) * 55}%, transparent)`,
                      }}
                    >
                      {cell}
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
