"use client"

import { useEffect, useMemo, useState } from "react"
import { Loader2, Plus } from "lucide-react"

import { ConsoleShell } from "@/components/layout/console-shell"
import {
  AliasPill,
  PlatformMetadataLine,
  RegistryEmpty,
  RegistryLink,
  RegistryPageHeader,
  RegistrySurface,
  RegistryTable,
  RegistryTd,
  RegistryTh,
  RegistryThead,
  RegistryToolbar,
  RegistryTr,
} from "@/components/console/registry"
import { Button } from "@/components/ui/button"
import { fetchModels } from "@/lib/api/metrics"
import { formatShortDate } from "@/lib/console/format"
import type { ModelSummary } from "@/lib/constants/metrics"

const statusOrder = ["production", "candidate", "rejected", "archived"]

export default function ModelsPage() {
  const [rows, setRows] = useState<ModelSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [stageFilter, setStageFilter] = useState("all")

  useEffect(() => {
    fetchModels()
      .then((models) => {
        setRows(models)
        if (models.length === 0) {
          setNotice("Chưa có model trong registry.")
        }
      })
      .catch((err) => {
        setRows([])
        setNotice(err instanceof Error ? err.message : "Không tải được model registry.")
      })
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

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return sorted.filter((row) => {
      if (stageFilter !== "all" && (row.stage ?? row.status).toLowerCase() !== stageFilter.toLowerCase()) {
        return false
      }
      if (!q) return true
      return (
        row.version.toLowerCase().includes(q) ||
        (row.alias ?? "").toLowerCase().includes(q) ||
        (row.stage ?? "").toLowerCase().includes(q)
      )
    })
  }, [sorted, search, stageFilter])

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <RegistryPageHeader
          title="Registered Models"
          metadata={<PlatformMetadataLine />}
          actions={
            <Button size="sm" disabled>
              <Plus className="size-3.5" />
              Register model
            </Button>
          }
        />

        {loading ? (
          <div className="flex items-center gap-2 py-8 text-[13px] text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading registry…
          </div>
        ) : (
          <RegistrySurface
            notice={notice}
            toolbar={
              <RegistryToolbar
                search={search}
                onSearchChange={setSearch}
                searchPlaceholder="Filter registered models by name"
                filters={[
                  {
                    label: "Stage",
                    value: stageFilter,
                    onChange: setStageFilter,
                    options: [
                      { label: "All stages", value: "all" },
                      { label: "Production", value: "production" },
                      { label: "Training", value: "training" },
                    ],
                  },
                ]}
              />
            }
          >
            {filtered.length === 0 ? (
              <RegistryEmpty
                title="No registered models"
                description="Train and register a model to manage champion and challenger aliases."
              />
            ) : (
              <RegistryTable>
                <RegistryThead>
                  <tr>
                    <RegistryTh>Name</RegistryTh>
                    <RegistryTh>Latest version</RegistryTh>
                    <RegistryTh>Aliased versions</RegistryTh>
                    <RegistryTh>Stage</RegistryTh>
                    <RegistryTh>Last modified</RegistryTh>
                  </tr>
                </RegistryThead>
                <tbody>
                  {filtered.map((row) => (
                    <RegistryTr key={row.version}>
                      <RegistryTd>
                        <RegistryLink href={`/models/${encodeURIComponent(row.version)}`}>
                          {row.version}
                        </RegistryLink>
                      </RegistryTd>
                      <RegistryTd>
                        {row.epoch > 0 ? (
                          <RegistryLink href={`/models/${encodeURIComponent(row.version)}`}>
                            Version {row.epoch}
                          </RegistryLink>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </RegistryTd>
                      <RegistryTd>
                        {row.alias ? (
                          <div className="flex flex-wrap items-center gap-2">
                            <AliasPill alias={row.alias} />
                            {row.epoch > 0 ? (
                              <span className="text-[12px] text-muted-foreground">
                                Version {row.epoch}
                              </span>
                            ) : null}
                          </div>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </RegistryTd>
                      <RegistryTd muted>{row.stage ?? row.status}</RegistryTd>
                      <RegistryTd muted>
                        {row.promoted_at ? formatShortDate(row.promoted_at) : "—"}
                      </RegistryTd>
                    </RegistryTr>
                  ))}
                </tbody>
              </RegistryTable>
            )}
          </RegistrySurface>
        )}
      </section>
    </ConsoleShell>
  )
}
