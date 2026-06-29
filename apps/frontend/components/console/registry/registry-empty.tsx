import { FlaskConical } from "lucide-react"

import { cn } from "@/lib/utils"

export function RegistryEmpty({
  title,
  description,
  action,
  className,
}: {
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center px-6 py-14 text-center", className)}>
      <FlaskConical className="mb-3 size-10 text-muted-foreground/25" strokeWidth={1.25} />
      <p className="text-[13px] font-medium text-foreground">{title}</p>
      {description ? (
        <p className="mt-1 max-w-sm text-[12px] text-muted-foreground">{description}</p>
      ) : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}
