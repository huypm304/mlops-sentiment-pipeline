"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"

import { ConsoleShell } from "@/components/layout/console-shell"
import { SectionHeader } from "@/components/console/section-header"
import { TableCard, ConsoleTable, ConsoleThead, ConsoleTh, ConsoleTr, ConsoleTd } from "@/components/console/table-card"
import { StatusBadge } from "@/components/console/status-badge"
import { fetchModels } from "@/lib/api/metrics"
import type { ModelSummary } from "@/lib/constants/metrics"

const statusOrder = ["production", "candidate", "rejected", "archived"]

export default function ModelsPage() {
  const [rows, setRows] = useState<ModelSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchModels()
      .then(setRows)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load models"))
      .finally(() => setLoading(false))
  }, [])

  const sorted = useMemo(
    () =>
      [...rows].sort((a, b) => {
        const ai = statusOrder.indexOf(a.status)
        const bi = statusOrder.indexOf(b.status)
        return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
      }),
    [rows],
  )

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <SectionHeader title="Models" description="Model registry." />

        <TableCard
          title="Model registry"
          loading={loading}
          loadingLabel="Loading models"
          error={error}
          empty={!loading && !error && sorted.length === 0}
          emptyLabel="No models found."
        >
          <ConsoleTable>
            <ConsoleThead>
              <tr>
                <ConsoleTh>Version</ConsoleTh>
                <ConsoleTh>Status</ConsoleTh>
                <ConsoleTh align="right">Global F1</ConsoleTh>
                <ConsoleTh align="right">Primary metric</ConsoleTh>
                <ConsoleTh>Lineage</ConsoleTh>
              </tr>
            </ConsoleThead>
            <tbody>
              {sorted.map((row) => (
                <ConsoleTr key={row.version}>
                  <ConsoleTd>
                    <Link href={`/models/${encodeURIComponent(row.version)}`} className="font-medium hover:underline">
                      {row.version}
                    </Link>
                  </ConsoleTd>
                  <ConsoleTd><StatusBadge value={row.status} /></ConsoleTd>
                  <ConsoleTd align="right" numeric>{(row.global_f1 * 100).toFixed(1)}%</ConsoleTd>
                  <ConsoleTd align="right" numeric>{(row.tas_relaxed_f1 * 100).toFixed(1)}%</ConsoleTd>
                  <ConsoleTd mono muted>{row.encoder}</ConsoleTd>
                </ConsoleTr>
              ))}
            </tbody>
          </ConsoleTable>
        </TableCard>
      </section>
    </ConsoleShell>
  )
}
