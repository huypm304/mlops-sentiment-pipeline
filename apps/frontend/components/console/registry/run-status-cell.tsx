import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react"

import { formatRelativeTime } from "@/lib/console/format"
import { cn } from "@/lib/utils"

function StatusIcon({ status }: { status: string }) {
  const key = status.toLowerCase()
  if (key === "succeeded" || key === "success") {
    return <CheckCircle2 className="size-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
  }
  if (key === "running") {
    return <Loader2 className="size-3.5 shrink-0 animate-spin text-sky-600 dark:text-sky-400" />
  }
  if (key === "failed") {
    return <XCircle className="size-3.5 shrink-0 text-red-600 dark:text-red-400" />
  }
  return <Circle className="size-3.5 shrink-0 text-muted-foreground" />
}

export function RunStatusCell({
  status,
  timestamp,
  className,
}: {
  status: string
  timestamp?: string | null
  className?: string
}) {
  const label = status.replace(/_/g, " ")
  return (
    <div className={cn("flex flex-col gap-0.5", className)}>
      <span className="inline-flex items-center gap-1.5 text-[13px] capitalize text-foreground">
        <StatusIcon status={status} />
        {label}
      </span>
      {timestamp ? (
        <span className="pl-5 text-[11px] text-muted-foreground">{formatRelativeTime(timestamp)}</span>
      ) : null}
    </div>
  )
}
