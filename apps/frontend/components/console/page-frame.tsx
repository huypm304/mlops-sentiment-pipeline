import Link from "next/link"
import { ChevronRight } from "lucide-react"

import { cn } from "@/lib/utils"

export function KpiStrip({
  items,
  className,
}: {
  items: { label: string; value: string; hint?: string; tone?: "neutral" | "ok" | "warn" | "bad" }[]
  className?: string
}) {
  return (
    <div
      className={cn(
        "grid divide-x divide-border overflow-hidden rounded-md border border-border bg-card sm:grid-cols-2 lg:grid-cols-5",
        className,
      )}
    >
      {items.map((item) => (
        <div key={item.label} className="px-3 py-2.5">
          <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
            {item.label}
          </p>
          <p
            className={cn(
              "mt-0.5 font-mono text-sm font-semibold tabular-nums",
              item.tone === "ok" && "text-emerald-400",
              item.tone === "warn" && "text-amber-400",
              item.tone === "bad" && "text-red-400",
            )}
          >
            {item.value}
          </p>
          {item.hint ? (
            <p className="mt-0.5 text-[10px] text-muted-foreground">{item.hint}</p>
          ) : null}
        </div>
      ))}
    </div>
  )
}

export function PageFrame({
  title,
  description,
  breadcrumbs,
  actions,
  children,
}: {
  title: string
  description?: string
  breadcrumbs?: { label: string; href?: string }[]
  actions?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section className="space-y-4">
      {breadcrumbs && breadcrumbs.length > 0 ? (
        <nav className="flex items-center gap-1 text-[11px] text-muted-foreground">
          {breadcrumbs.map((crumb, i) => (
            <span key={`${crumb.label}-${i}`} className="inline-flex items-center gap-1">
              {i > 0 ? <ChevronRight className="size-3 opacity-50" /> : null}
              {crumb.href ? (
                <Link href={crumb.href} className="hover:text-foreground">
                  {crumb.label}
                </Link>
              ) : (
                <span className="text-foreground/80">{crumb.label}</span>
              )}
            </span>
          ))}
        </nav>
      ) : null}

      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-border/60 pb-3">
        <div>
          <h1 className="text-base font-semibold tracking-tight">{title}</h1>
          {description ? (
            <p className="mt-0.5 max-w-3xl text-[13px] leading-relaxed text-muted-foreground">
              {description}
            </p>
          ) : null}
        </div>
        {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
      </header>

      {children}
    </section>
  )
}

export function ActionToolbar({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap gap-2 rounded-md border border-border/70 bg-muted/20 p-2">
      {children}
    </div>
  )
}

export function ActionLink({
  href,
  children,
}: {
  href: string
  children: React.ReactNode
}) {
  return (
    <Link
      href={href}
      className="inline-flex items-center rounded border border-border bg-background px-2.5 py-1.5 text-[12px] font-medium text-foreground/90 transition-colors hover:bg-muted/50"
    >
      {children}
    </Link>
  )
}
