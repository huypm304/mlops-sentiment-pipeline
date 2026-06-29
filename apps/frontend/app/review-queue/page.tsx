"use client"

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

import { ConsoleShell } from "@/components/layout/console-shell"
import {
  PlatformMetadataLine,
  RegistryEmpty,
  RegistryPageHeader,
  RegistrySurface,
  RegistryTable,
  RegistryTd,
  RegistryTh,
  RegistryThead,
  RegistryTr,
} from "@/components/console/registry"
import { fetchReviewQueue, type ReviewQueueItem } from "@/lib/api/analytics"
import { cn } from "@/lib/utils"

const STATUS_STYLES: Record<string, string> = {
  Pending: "text-amber-700 dark:text-amber-400",
  "In review": "text-sky-700 dark:text-sky-400",
  Resolved: "text-emerald-700 dark:text-emerald-400",
}

const GUARDRAIL_STYLES: Record<string, string> = {
  WARN: "text-amber-700 dark:text-amber-400",
  REVIEW: "text-sky-700 dark:text-sky-400",
  REJECT: "text-red-700 dark:text-red-400",
}

export default function ReviewQueuePage() {
  const [items, setItems] = useState<ReviewQueueItem[]>([])
  const [openCount, setOpenCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    fetchReviewQueue()
      .then((res) => {
        setItems(res.items)
        setOpenCount(res.open_count)
      })
      .catch((err) =>
        setNotice(err instanceof Error ? err.message : "Review queue unavailable"),
      )
      .finally(() => setLoading(false))
  }, [])

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <RegistryPageHeader
          title="Review Queue"
          metadata={
            <>
              <PlatformMetadataLine />
              {openCount > 0 ? (
                <p className="mt-0.5">{openCount} open items flagged by guardrails</p>
              ) : null}
            </>
          }
        />

        {loading ? (
          <div className="flex items-center gap-2 py-8 text-[13px] text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading review queue…
          </div>
        ) : (
          <RegistrySurface notice={notice}>
            {items.length === 0 ? (
              <RegistryEmpty
                title="Queue is empty"
                description="Flagged predictions appear here after inference runs."
              />
            ) : (
              <RegistryTable>
                <RegistryThead>
                  <tr>
                    <RegistryTh>Time</RegistryTh>
                    <RegistryTh>Text</RegistryTh>
                    <RegistryTh>Reason</RegistryTh>
                    <RegistryTh>Model</RegistryTh>
                    <RegistryTh align="right">Confidence</RegistryTh>
                    <RegistryTh>Guardrail</RegistryTh>
                    <RegistryTh>Status</RegistryTh>
                  </tr>
                </RegistryThead>
                <tbody>
                  {items.map((row) => (
                    <RegistryTr key={row.id}>
                      <RegistryTd mono muted className="whitespace-nowrap">
                        {row.time}
                      </RegistryTd>
                      <RegistryTd className="max-w-[240px] truncate">{row.text}</RegistryTd>
                      <RegistryTd muted>{row.reason}</RegistryTd>
                      <RegistryTd mono>{row.model_version}</RegistryTd>
                      <RegistryTd align="right" numeric>
                        {row.confidence}
                      </RegistryTd>
                      <RegistryTd className={cn("text-[12px] font-medium", GUARDRAIL_STYLES[row.guardrail])}>
                        {row.guardrail}
                      </RegistryTd>
                      <RegistryTd className={cn("text-[12px] font-medium", STATUS_STYLES[row.status])}>
                        {row.status}
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
