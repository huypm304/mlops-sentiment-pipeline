import { cn } from "@/lib/utils"

const statusVariants: Record<string, string> = {
  production: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  candidate: "border-sky-500/30 bg-sky-500/10 text-sky-400",
  champion: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  challenger: "border-sky-500/30 bg-sky-500/10 text-sky-400",
  rejected: "border-red-500/30 bg-red-500/10 text-red-400",
  archived: "border-border bg-muted/40 text-muted-foreground",
  approved: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  audited: "border-sky-500/30 bg-sky-500/10 text-sky-400",
  pending: "border-amber-500/30 bg-amber-500/10 text-amber-400",
  pass: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  running: "border-sky-500/30 bg-sky-500/10 text-sky-400",
  succeeded: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  failed: "border-red-500/30 bg-red-500/10 text-red-400",
  stopped: "border-border bg-muted/40 text-muted-foreground",
  timed_out: "border-amber-500/30 bg-amber-500/10 text-amber-400",
  aborted: "border-border bg-muted/40 text-muted-foreground",
  stable: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  ok: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  warning: "border-amber-500/30 bg-amber-500/10 text-amber-400",
  warn: "border-amber-500/30 bg-amber-500/10 text-amber-400",
  alert: "border-red-500/30 bg-red-500/10 text-red-400",
  drift: "border-red-500/30 bg-red-500/10 text-red-400",
  healthy: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  degraded: "border-amber-500/30 bg-amber-500/10 text-amber-400",
  down: "border-red-500/30 bg-red-500/10 text-red-400",
  unknown: "border-border bg-muted/40 text-muted-foreground",
  review: "border-sky-500/30 bg-sky-500/10 text-sky-400",
  reject: "border-red-500/30 bg-red-500/10 text-red-400",
  insufficient_data: "border-border bg-muted/40 text-muted-foreground",
}

const DEFAULT_VARIANT = "border-border bg-muted/40 text-muted-foreground"

interface StatusBadgeProps {
  value: string
  className?: string
}

export function StatusBadge({ value, className }: StatusBadgeProps) {
  const safe = (value || "unknown").toString()
  const key = safe.toLowerCase().trim().replace(/\s+/g, "_")
  const colors = statusVariants[key] ?? DEFAULT_VARIANT
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-1.5 py-0.5 font-mono text-[10px] font-medium uppercase tracking-wide",
        colors,
        className,
      )}
    >
      {safe.replace(/_/g, " ")}
    </span>
  )
}
