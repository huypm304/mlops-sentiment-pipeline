"use client"

import { useEffect, useState } from "react"

import { fetchPlatformContext } from "@/lib/api/platform"
import { fetchHealth } from "@/lib/api/runtime"
import { cn } from "@/lib/utils"

function MetaItem({
  label,
  value,
  tone = "neutral",
}: {
  label: string
  value: string
  tone?: "neutral" | "ok" | "warn" | "bad"
}) {
  return (
    <span className="inline-flex items-center gap-1 text-[12px] text-muted-foreground">
      <span>{label}</span>
      <span
        className={cn(
          "font-medium",
          tone === "neutral" && "text-foreground",
          tone === "ok" && "text-emerald-700 dark:text-emerald-400",
          tone === "warn" && "text-amber-700 dark:text-amber-400",
          tone === "bad" && "text-red-700 dark:text-red-400",
        )}
      >
        {value}
      </span>
    </span>
  )
}

export function OpsContextBar() {
  const [env, setEnv] = useState("—")
  const [api, setApi] = useState("—")

  useEffect(() => {
    fetchPlatformContext()
      .then((ctx) => {
        setEnv(ctx.environment)
        setApi(ctx.api_status === "healthy" ? "Healthy" : ctx.api_status)
      })
      .catch(() => {
        fetchHealth()
          .then((h) => setApi(h.endpoint_health === "healthy" ? "Healthy" : "Down"))
          .catch(() => setApi("Down"))
      })
  }, [])

  const apiTone = api === "Healthy" ? "ok" : api === "degraded" ? "warn" : api === "—" ? "neutral" : "bad"

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px]">
      <MetaItem label="ENV" value={env} />
      <MetaItem label="API" value={api} tone={apiTone} />
    </div>
  )
}
