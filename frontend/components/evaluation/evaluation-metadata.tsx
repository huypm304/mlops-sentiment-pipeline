import type { ModelEvaluation } from "@/types/evaluation"
import { metricLabel } from "@/lib/constants/metrics"

type EvaluationMetadataProps = {
  evaluation: ModelEvaluation
}

export function EvaluationMetadata({ evaluation }: EvaluationMetadataProps) {
  const items = [
    { label: "Checkpoint", value: evaluation.training.checkpoint },
    { label: "Encoder", value: evaluation.training.encoder },
    {
      label: "Training",
      value: `${evaluation.training.epochs} epochs · batch ${evaluation.training.batchSize}`,
    },
    {
      label: "Best epoch",
      value: evaluation.epoch
        ? `${evaluation.epoch} (${evaluation.phase ?? ""})`
        : "—",
    },
    {
      label: metricLabel("tas_relaxed_f1"),
      value: evaluation.scores
        ? `${(evaluation.scores.tas_relaxed_f1 * 100).toFixed(1)}%`
        : "—",
    },
    {
      label: "Test samples",
      value: evaluation.dataset.testSamples.toLocaleString(),
    },
  ]

  return (
    <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((item) => (
        <div key={item.label}>
          <dt className="text-[10px] text-muted-foreground">{item.label}</dt>
          <dd className="mt-0.5 text-sm font-medium">{item.value}</dd>
        </div>
      ))}
    </dl>
  )
}
