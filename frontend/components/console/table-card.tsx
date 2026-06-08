import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface TableCardProps {
  title: string
  /** Optional element rendered on the right side of the card header */
  action?: React.ReactNode
  loading?: boolean
  loadingLabel?: string
  error?: string | null
  /** Pass `true` when the data array is empty */
  empty?: boolean
  emptyLabel?: string
  className?: string
  children?: React.ReactNode
}

/**
 * Consistent card wrapper for tabular data across all console pages.
 *
 * Usage:
 * ```tsx
 * <TableCard title="Datasets" loading={loading} empty={rows.length === 0}>
 *   <table>…</table>
 * </TableCard>
 * ```
 * `children` is rendered inside an `overflow-x-auto` wrapper.
 */
export function TableCard({
  title,
  action,
  loading,
  loadingLabel = "Loading",
  error,
  empty,
  emptyLabel = "No data.",
  className,
  children,
}: TableCardProps) {
  return (
    <div className={cn("rounded-md border border-border bg-card", className)}>
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <p className="text-sm font-semibold">{title}</p>
        {action && <div className="shrink-0">{action}</div>}
      </div>

      {loading ? (
        <div className="flex items-center gap-2 px-4 py-8 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          {loadingLabel}
        </div>
      ) : error ? (
        <p className="px-4 py-6 text-sm text-red-500">{error}</p>
      ) : empty ? (
        <p className="px-4 py-6 text-sm text-muted-foreground">{emptyLabel}</p>
      ) : (
        <div className="overflow-x-auto">{children}</div>
      )}
    </div>
  )
}

/** Standard table element — full-width, small text */
export function ConsoleTable({ className, ...props }: React.ComponentProps<"table">) {
  return <table className={cn("w-full text-sm", className)} {...props} />
}

/** Standard <thead> row with consistent styling */
export function ConsoleThead({ className, ...props }: React.ComponentProps<"thead">) {
  return <thead className={cn("border-b border-border text-left text-xs text-muted-foreground", className)} {...props} />
}

/** Standard <th> cell */
export function ConsoleTh({
  align = "left",
  className,
  ...props
}: React.ComponentProps<"th"> & { align?: "left" | "right" | "center" }) {
  return (
    <th
      className={cn(
        "px-4 py-2 font-medium",
        align === "right" && "text-right",
        align === "center" && "text-center",
        className,
      )}
      {...props}
    />
  )
}

/** Standard <tbody> row */
export function ConsoleTr({ className, ...props }: React.ComponentProps<"tr">) {
  return <tr className={cn("border-b border-border/60 last:border-0", className)} {...props} />
}

/** Standard <td> cell */
export function ConsoleTd({
  align = "left",
  muted,
  mono,
  numeric,
  className,
  ...props
}: React.ComponentProps<"td"> & {
  align?: "left" | "right" | "center"
  muted?: boolean
  mono?: boolean
  numeric?: boolean
}) {
  return (
    <td
      className={cn(
        "px-4 py-2.5",
        align === "right" && "text-right",
        align === "center" && "text-center",
        muted && "text-muted-foreground",
        mono && "font-mono text-xs",
        numeric && "tabular-nums",
        className,
      )}
      {...props}
    />
  )
}
