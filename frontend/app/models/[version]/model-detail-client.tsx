"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

import { ConsoleShell } from "@/components/layout/console-shell"
import { SectionHeader } from "@/components/console/section-header"
import { StatusBadge } from "@/components/console/status-badge"
import { fetchModelEvaluation } from "@/lib/api/metrics"
import type { ModelEvaluation } from "@/types/evaluation"

export function ModelDetailClient({ version }: { version: string }) {
  const [model, setModel] = useState<ModelEvaluation | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchModelEvaluation(version)
      .then(setModel)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load model detail"))
      .finally(() => setLoading(false))
  }, [version])

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <SectionHeader title="Model detail" description={version}>
          <Link href="/models" className="text-xs text-muted-foreground hover:underline">Back to models</Link>
        </SectionHeader>

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading model
          </div>
        ) : error ? (
          <p className="text-sm text-red-500">{error}</p>
        ) : !model ? (
          <p className="text-sm text-muted-foreground">Model not found.</p>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            <section className="rounded-md border border-border bg-card">
              <div className="border-b border-border px-4 py-3"><h2 className="text-sm font-semibold">Model card</h2></div>
              <div className="space-y-2 px-4 py-4 text-sm">
                <Row label="Version" value={model.version} mono />
                <div className="flex items-center justify-between gap-3 rounded border border-border/70 px-3 py-2">
                  <span className="text-muted-foreground">Status</span>
                  <StatusBadge value={model.status} />
                </div>
                <Row label="Encoder" value={model.training.encoder} mono />
                <Row label="Checkpoint" value={model.training.checkpoint} mono />
              </div>
            </section>

            <section className="rounded-md border border-border bg-card">
              <div className="border-b border-border px-4 py-3"><h2 className="text-sm font-semibold">Metrics</h2></div>
              <div className="space-y-2 px-4 py-4 text-sm">
                <Row label="Global F1" value={`${((model.scores?.global_f1 ?? 0) * 100).toFixed(1)}%`} />
                <Row label="Span F1" value={`${((model.scores?.span_f1 ?? 0) * 100).toFixed(1)}%`} />
                <Row label="Sent Matched F1" value={`${((model.scores?.sent_matched_f1 ?? 0) * 100).toFixed(1)}%`} />
                <Row label="Latency" value={`${model.inferenceLatencyMs} ms`} />
              </div>
            </section>

            <section className="rounded-md border border-border bg-card">
              <div className="border-b border-border px-4 py-3"><h2 className="text-sm font-semibold">Artifacts</h2></div>
              <div className="px-4 py-4 text-sm text-muted-foreground">
                <p>Checkpoint, evaluation report, confusion matrix, and metadata are linked via registry output.</p>
              </div>
            </section>

            <section className="rounded-md border border-border bg-card">
              <div className="border-b border-border px-4 py-3"><h2 className="text-sm font-semibold">Lineage & promotion history</h2></div>
              <div className="space-y-2 px-4 py-4 text-sm">
                <Row label="Dataset version" value={model.dataset.version} />
                <Row label="Registered at" value={new Date(model.registeredAt).toLocaleString()} />
                <Row label="Evaluated at" value={new Date(model.evaluatedAt).toLocaleString()} />
              </div>
            </section>
          </div>
        )}
      </section>
    </ConsoleShell>
  )
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded border border-border/70 px-3 py-2">
      <span className="text-muted-foreground">{label}</span>
      <span className={mono ? "font-mono text-xs" : ""}>{value}</span>
    </div>
  )
}
