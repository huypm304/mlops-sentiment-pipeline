"use client"

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  XAxis,
  YAxis,
} from "recharts"

import { AspectMetricsTable } from "@/components/evaluation/aspect-metrics-table"
import { ConfusionMatrixView } from "@/components/evaluation/confusion-matrix"
import { EvaluationMetadata } from "@/components/evaluation/evaluation-metadata"
import { MetricsOverview } from "@/components/evaluation/metrics-overview"
import { ChartPanel } from "@/components/dashboard/chart-panel"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import type { TrainingHistoryPoint } from "@/lib/api/metrics"
import type { ModelEvaluation } from "@/types/evaluation"

const f1ChartConfig = {
  composite: { label: "Composite", color: "var(--chart-1)" },
  span_f1: { label: "Span F1", color: "var(--chart-2)" },
  sent_f1: { label: "Sentiment F1", color: "var(--chart-3)" },
  glob_f1: { label: "Global F1", color: "var(--chart-4)" },
} satisfies ChartConfig

type EvaluationReportProps = {
  evaluation: ModelEvaluation
  history: TrainingHistoryPoint[]
}

export function EvaluationReport({ evaluation, history }: EvaluationReportProps) {
  const bestEpoch = evaluation.epoch

  return (
    <div className="space-y-6">
      {evaluation.scores ? (
        <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <ScoreCard label="Best epoch" value={String(bestEpoch ?? "—")} raw />
          <ScoreCard label="Composite" value={evaluation.scores.composite} />
          <ScoreCard label="Span F1" value={evaluation.scores.span_f1} />
          <ScoreCard label="Sentiment F1" value={evaluation.scores.sent_f1} />
          <ScoreCard label="Global F1" value={evaluation.scores.glob_f1} />
        </dl>
      ) : null}

      <ChartPanel
        title="Evaluation report"
        description={`Dataset · ${evaluation.dataset.version} · checkpoint ${evaluation.training.checkpoint}`}
      >
        <EvaluationMetadata evaluation={evaluation} />
      </ChartPanel>

      <ChartPanel title="Training curves" description="Validation F1 per epoch (train_log.csv)">
        <ChartContainer config={f1ChartConfig} className="h-[260px] w-full">
          <LineChart data={history}>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis dataKey="epoch" tick={{ fontSize: 10 }} />
            <YAxis
              domain={[0, 1]}
              tickFormatter={(v) => `${(Number(v) * 100).toFixed(0)}%`}
              tick={{ fontSize: 10 }}
              width={36}
            />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="composite"
              stroke="var(--color-composite)"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="span_f1"
              stroke="var(--color-span_f1)"
              strokeWidth={1.5}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="sent_f1"
              stroke="var(--color-sent_f1)"
              strokeWidth={1.5}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="glob_f1"
              stroke="var(--color-glob_f1)"
              strokeWidth={1.5}
              dot={false}
            />
          </LineChart>
        </ChartContainer>
      </ChartPanel>

      <ChartPanel title="Loss curve" description="Training loss per epoch">
        <ChartContainer
          config={{ train_loss: { label: "Loss", color: "var(--chart-1)" } }}
          className="h-[200px] w-full"
        >
          <LineChart data={history}>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis dataKey="epoch" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} width={40} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Line
              type="monotone"
              dataKey="train_loss"
              stroke="var(--color-train_loss)"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ChartContainer>
      </ChartPanel>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartPanel title="Span sentiment metrics" description="Precision · recall · F1">
          <MetricsOverview title="" metrics={evaluation.sentiment} />
        </ChartPanel>
        <ChartPanel title="Global sentiment metrics" description="Document-level head">
          <MetricsOverview
            title=""
            metrics={evaluation.globalSentiment ?? evaluation.aspectPolarity}
          />
        </ChartPanel>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartPanel title="Confusion matrix" description="Span sentiment · test set">
          <ConfusionMatrixView title="" data={evaluation.confusionMatrix} />
        </ChartPanel>
        <ChartPanel
          title="Per-aspect metrics"
          description={`Best epoch ${bestEpoch ?? "—"} · span & sentiment F1`}
        >
          <AspectMetricsTable aspects={evaluation.perAspect} />
        </ChartPanel>
      </div>

      <ChartPanel title="Aspect extraction" description="Span detection F1 (validation)">
        <MetricsOverview title="" metrics={evaluation.aspectExtraction} />
      </ChartPanel>
    </div>
  )
}

function ScoreCard({
  label,
  value,
  raw,
}: {
  label: string
  value: number | string
  raw?: boolean
}) {
  const display =
    raw || typeof value === "string"
      ? String(value)
      : `${(value * 100).toFixed(1)}%`

  return (
    <div className="rounded-lg border border-white/[0.08] bg-white/[0.02] px-4 py-3">
      <dt className="text-[11px] text-muted-foreground">{label}</dt>
      <dd className="mt-1 font-mono text-xl font-semibold tabular-nums">{display}</dd>
    </div>
  )
}
