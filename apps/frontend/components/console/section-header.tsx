import { cn } from "@/lib/utils"

interface SectionHeaderProps {
  title: string
  description?: string
  className?: string
  children?: React.ReactNode
}

/**
 * Consistent page-level section header used across all console pages.
 * Place at the top of a <section className="space-y-4"> block.
 */
export function SectionHeader({ title, description, className, children }: SectionHeaderProps) {
  return (
    <header className={cn("flex items-start justify-between gap-4", className)}>
      <div className="space-y-0.5">
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      {children && <div className="shrink-0">{children}</div>}
    </header>
  )
}
