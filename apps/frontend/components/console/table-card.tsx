import { Loader2 } from "lucide-react"

import {
  RegistryNotice,
  RegistrySurface,
  RegistryTable,
  RegistryTd,
  RegistryTh,
  RegistryThead,
  RegistryTr,
} from "@/components/console/registry"
import { cn } from "@/lib/utils"

import type { TableCardProps } from "./table-card-types"

export type { TableCardProps }

/**
 * Legacy wrapper — prefer RegistrySurface + RegistryTable directly.
 */
export function TableCard({
  title,
  action,
  toolbar,
  loading,
  loadingLabel = "Loading",
  notice,
  noticeTone = "warn",
  empty,
  emptyLabel = "No data.",
  className,
  children,
}: TableCardProps) {
  const showBody = Boolean(children) && !loading

  if (!title && !toolbar && !notice && !loading) {
    return (
      <RegistrySurface className={className} toolbar={toolbar}>
        {showBody ? children : empty ? (
          <p className="px-3 py-3 text-[12px] text-muted-foreground">{emptyLabel}</p>
        ) : null}
      </RegistrySurface>
    )
  }

  return (
    <div className={cn("registry-surface", className)}>
      {title ? (
        <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
          <p className="text-[13px] font-semibold">{title}</p>
          {action}
        </div>
      ) : null}
      {notice ? <RegistryNotice message={notice} tone={noticeTone} /> : null}
      {toolbar}
      {loading ? (
        <div className="flex items-center gap-2 px-3 py-3 text-[13px] text-muted-foreground">
          <Loader2 className="size-3.5 animate-spin" />
          {loadingLabel}
        </div>
      ) : showBody ? (
        <div className="overflow-x-auto">{children}</div>
      ) : empty ? (
        <p className="px-3 py-3 text-[12px] text-muted-foreground">{emptyLabel}</p>
      ) : null}
    </div>
  )
}

export {
  RegistryTable as ConsoleTable,
  RegistryThead as ConsoleThead,
  RegistryTh as ConsoleTh,
  RegistryTr as ConsoleTr,
  RegistryTd as ConsoleTd,
}
