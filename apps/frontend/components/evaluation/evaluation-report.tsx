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
import { metricLabel } from "@/lib/constants/metrics"
import type { TrainingHistoryPoint } from "@/lib/api/metrics"
import type { ModelEvaluation } from "@/types/evaluation"

const f1ChartConfig = {
  tas_relaxed_f1: { label: metricLabel("tas_relaxed_f1"), color: "var(--chart-1)" },
  tas_strict_f1: { label: metricLabel("tas_strict_f1"), color: "var(--chart-5)" },
  span_f1: { label: metricLabel("span_f1"), color: "var(--chart-2)" },
  sent_matched_f1: { label: metricLabel("sent_matched_f1"), color: "var(--chart-3)" },
  sent_goldspan_f1: { label: metricLabel("sent_goldspan_f1"), color: "var(--chart-6)" },
  global_f1: { label: metricLabel("global_f1"), color: "var(--chart-4)" },
} satisfies ChartConfig

type EvaluationReportProps = {
  evaluation: ModelEvaluation
  history: TrainingHistoryPoint[]
}

export function EvaluationReport({ evaluation, history }: EvaluationReportProps) {
  const bestEpoch = evaluation.epoch
  const scores = evaluation.scores

  return (
    <div className="space-y-6">
      {scores ? (
        <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
          <ScoreCard label="Best epoch" value={String(bestEpoch ?? "—")} raw />
          <ScoreCard label={metricLabel("tas_relaxed_f1")} value={scores.tas_relaxed_f1} />
          <ScoreCard label={metricLabel("tas_strict_f1")} value={scores.tas_strict_f1} />
          <ScoreCard label={metricLabel("span_f1")} value={scores.span_f1} />
          <ScoreCard label={metricLabel("sent_matched_f1")} value={scores.sent_matched_f1} />
          <ScoreCard label={metricLabel("sent_goldspan_f1")} value={scores.sent_goldspan_f1} />
          <ScoreCard label={metricLabel("global_f1")} value={scores.global_f1} />
        </dl>
      ) : null}

      <ChartPanel
        title="Evaluation report"
        description={`Dataset · ${evaluation.dataset.version} · checkpoint ${evaluation.training.checkpoint}`}
      >
        <EvaluationMetadata evaluation={evaluation} />
      </ChartPanel>

      <ChartPanel title="Training curves" description="Validation F1 per epoch (train_log.csv)">
        <ChartContainer config={f1ChartConfig} className="h-[280px] w-full">
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
            <Line type="monotone" dataKey="tas_relaxed_f1" stroke="var(--color-tas_relaxed_f1)" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="tas_strict_f1" stroke="var(--color-tas_strict_f1)" strokeWidth={1.5} dot={false} />
            <Line type="monotone" dataKey="span_f1" stroke="var(--color-span_f1)" strokeWidth={1.5} dot={false} />
            <Line type="monotone" dataKey="sent_matched_f1" stroke="var(--color-sent_matched_f1)" strokeWidth={1.5} dot={false} />
            <Line type="monotone" dataKey="sent_goldspan_f1" stroke="var(--color-sent_goldspan_f1)" strokeWidth={1.5} dot={false} />
            <Line type="monotone" dataKey="global_f1" stroke="var(--color-global_f1)" strokeWidth={1.5} dot={false} />
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
        <ChartPanel
          title="Span sentiment metrics"
          description="Sent@Matched · P/R/F1 từ train_log, accuracy từ confusion matrix"
        >
          <MetricsOverview title="" metrics={evaluation.sentiment} />
        </ChartPanel>
        <ChartPanel
          title="Global sentiment metrics"
          description="Document-level head · P/R/F1 từ train_log, accuracy từ confusion matrix"
        >
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

      <ChartPanel
        title="Aspect extraction"
        description="Span detection · P/R/F1 từ train_log (best epoch)"
      >
        <MetricsOverview title="" metrics={evaluation.aspectExtraction} showAccuracy={false} />
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
