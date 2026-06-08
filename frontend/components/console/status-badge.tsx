import { cn } from "@/lib/utils"

/**
 * Unified status badge for all entity types: models, datasets, runs, monitoring.
 * Pass `value` as the raw status string (any case). Display is always uppercase.
 */

const statusVariants: Record<string, string> = {
  // model registry
  production: "bg-emerald-50 text-emerald-700 border-emerald-200",
  candidate: "bg-sky-50 text-sky-700 border-sky-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
  archived: "bg-neutral-100 text-neutral-500 border-neutral-200",

  // dataset lifecycle
  approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
  audited: "bg-sky-50 text-sky-700 border-sky-200",
  pending: "bg-amber-50 text-amber-700 border-amber-200",

  // training runs
  succeeded: "bg-emerald-50 text-emerald-700 border-emerald-200",
  running: "bg-sky-50 text-sky-700 border-sky-200",
  failed: "bg-red-50 text-red-700 border-red-200",
  stopped: "bg-neutral-100 text-neutral-500 border-neutral-200",
  timed_out: "bg-amber-50 text-amber-700 border-amber-200",
  aborted: "bg-neutral-100 text-neutral-500 border-neutral-200",

  // drift / monitoring
  stable: "bg-emerald-50 text-emerald-700 border-emerald-200",
  warn: "bg-amber-50 text-amber-700 border-amber-200",
  drift: "bg-red-50 text-red-700 border-red-200",

  // api health
  healthy: "bg-emerald-50 text-emerald-700 border-emerald-200",
  degraded: "bg-amber-50 text-amber-700 border-amber-200",
  down: "bg-red-50 text-red-700 border-red-200",
  unknown: "bg-neutral-100 text-neutral-500 border-neutral-200",

  // guardrail / audit result
  pass: "bg-emerald-50 text-emerald-700 border-emerald-200",
  review: "bg-sky-50 text-sky-700 border-sky-200",
  reject: "bg-red-50 text-red-700 border-red-200",
}

const DEFAULT_VARIANT = "bg-neutral-100 text-neutral-500 border-neutral-200"

interface StatusBadgeProps {
  value: string
  className?: string
}

export function StatusBadge({ value, className }: StatusBadgeProps) {
  const key = value.toLowerCase().trim().replace(/\s+/g, "_")
  const colors = statusVariants[key] ?? DEFAULT_VARIANT
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-1.5 py-0.5 text-[11px] font-medium uppercase tracking-wide",
        colors,
        className,
      )}
    >
      {value.toUpperCase()}
    </span>
  )
}
