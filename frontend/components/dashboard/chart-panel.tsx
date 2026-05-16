import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

type ChartPanelProps = {
  title: ReactNode
  description?: string
  action?: ReactNode
  children: ReactNode
  className?: string
  contentClassName?: string
  noPadding?: boolean
}

export function ChartPanel({
  title,
  description,
  action,
  children,
  className,
  contentClassName,
  noPadding,
}: ChartPanelProps) {
  return (
    <section
      className={cn(
        "flex flex-col overflow-hidden rounded-lg border border-white/[0.08] bg-white/[0.02]",
        className
      )}
    >
      <div className="flex items-start justify-between gap-3 border-b border-white/[0.06] px-3.5 py-2.5">
        <div className="min-w-0">
          <h3 className="text-[13px] font-medium text-foreground">{title}</h3>
          {description ? (
            <p className="mt-0.5 text-[11px] leading-snug text-muted-foreground">
              {description}
            </p>
          ) : null}
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
      <div
        className={cn(
          !noPadding && "p-3.5 pt-2",
          "min-h-0 flex-1",
          contentClassName
        )}
      >
        {children}
      </div>
    </section>
  )
}
