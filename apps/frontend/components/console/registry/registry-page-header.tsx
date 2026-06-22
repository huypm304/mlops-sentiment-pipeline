"use client"

import { useEffect, useState } from "react"

import { fetchPlatformContext } from "@/lib/api/platform"
import { formatShortDate } from "@/lib/console/format"
import { cn } from "@/lib/utils"

export function RegistryPageHeader({
  title,
  metadata,
  actions,
  className,
}: {
  title: string
  metadata?: React.ReactNode
  actions?: React.ReactNode
  className?: string
}) {
  return (
    <header className={cn("border-b border-border pb-3", className)}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">{title}</h1>
        {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
      </div>
      {metadata ? <div className="mt-1 text-meta">{metadata}</div> : null}
    </header>
  )
}

export function PlatformMetadataLine({ className }: { className?: string }) {
  const [parts, setParts] = useState<string[]>([])
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    fetchPlatformContext()
      .then((ctx) => {
        setFailed(false)
        const line = [
          ctx.champion_model ? `Champion: ${ctx.champion_model}` : "Champion: —",
          ctx.active_dataset ? `Dataset: ${ctx.active_dataset}` : "Dataset: —",
          `Last training: ${formatShortDate(ctx.last_training_at)}`,
        ]
        setParts(line)
      })
      .catch(() => {
        setFailed(true)
        setParts([])
      })
  }, [])

  if (failed) {
    return <p className={cn("text-meta", className)}>Platform metadata unavailable</p>
  }

  if (parts.length === 0) return null

  return (
    <p className={cn("text-meta", className)}>
      {parts.join(" · ")}
    </p>
  )
}

export function RegistryNotice({
  message,
  tone = "warn",
}: {
  message: string
  tone?: "warn" | "error" | "info"
}) {
  return (
    <p
      className={cn(
        "border-b border-border px-3 py-1.5 text-[12px]",
        tone === "warn" && "bg-amber-50 text-amber-800 dark:bg-amber-500/10 dark:text-amber-300",
        tone === "error" && "bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-300",
        tone === "info" && "bg-muted text-muted-foreground",
      )}
    >
      {message}
    </p>
  )
}

export function RegistrySurface({
  notice,
  toolbar,
  children,
  className,
}: {
  notice?: string | null
  toolbar?: React.ReactNode
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn("registry-surface", className)}>
      {notice ? <RegistryNotice message={notice} /> : null}
      {toolbar}
      <div className="overflow-x-auto">{children}</div>
    </div>
  )
}
