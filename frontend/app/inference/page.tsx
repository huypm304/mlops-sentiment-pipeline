"use client"

import { useEffect, useState } from "react"

import { ConsoleShell } from "@/components/layout/console-shell"
import { SectionHeader } from "@/components/console/section-header"
import { TableCard, ConsoleTable, ConsoleThead, ConsoleTh, ConsoleTr, ConsoleTd } from "@/components/console/table-card"
import { InferencePlayground } from "@/components/admin/inference-playground"
import { fetchAnalytics, type AnalyticsPayload } from "@/lib/api/analytics"

export default function InferencePage() {
  const [analytics, setAnalytics] = useState<AnalyticsPayload | null>(null)

  useEffect(() => {
    fetchAnalytics(24).then(setAnalytics).catch(() => setAnalytics(null))
  }, [])

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <SectionHeader title="Inference" description="Text input, prediction output, and recent prediction records." />

        <InferencePlayground />

        <TableCard
          title="Recent predictions"
          empty={!analytics || analytics.recent_predictions.length === 0}
          emptyLabel="No prediction records."
        >
          <ConsoleTable>
            <ConsoleThead>
              <tr>
                <ConsoleTh>Time</ConsoleTh>
                <ConsoleTh>Text</ConsoleTh>
                <ConsoleTh>Model</ConsoleTh>
                <ConsoleTh align="right">Confidence</ConsoleTh>
              </tr>
            </ConsoleThead>
            <tbody>
              {analytics?.recent_predictions.slice(0, 12).map((row, idx) => (
                <ConsoleTr key={`${row.time}-${idx}`}>
                  <ConsoleTd muted mono>{row.time}</ConsoleTd>
                  <ConsoleTd>{row.text}</ConsoleTd>
                  <ConsoleTd mono>{row.model_version}</ConsoleTd>
                  <ConsoleTd align="right" numeric>{(row.confidence * 100).toFixed(1)}%</ConsoleTd>
                </ConsoleTr>
              ))}
            </tbody>
          </ConsoleTable>
        </TableCard>
      </section>
    </ConsoleShell>
  )
}
