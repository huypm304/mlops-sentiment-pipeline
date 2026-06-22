import { cn } from "@/lib/utils"

export function AliasPill({
  alias,
  className,
}: {
  alias: string
  className?: string
}) {
  const label = alias.startsWith("@") ? alias : `@ ${alias.toLowerCase()}`
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full bg-[#434343] px-2 py-0.5 font-mono text-[11px] font-medium text-white dark:bg-[#525252]",
        className,
      )}
    >
      {label}
    </span>
  )
}

export function AuditPill({
  label,
  className,
}: {
  label: string
  className?: string
}) {
  const key = label.toLowerCase()
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium",
        key === "pass" && "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-400",
        key === "running" && "border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-400",
        key === "pending" && "border-border bg-muted text-muted-foreground",
        key === "fail" && "border-red-200 bg-red-50 text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-400",
        className,
      )}
    >
      {label}
    </span>
  )
}
