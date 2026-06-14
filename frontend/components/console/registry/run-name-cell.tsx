import Link from "next/link"

import { appPath } from "@/lib/console/paths"
import { runDotColor } from "@/lib/console/format"
import { cn } from "@/lib/utils"

export function RunNameCell({
  name,
  href,
  status,
  className,
}: {
  name: string
  href: string
  status: string
  className?: string
}) {
  return (
    <div className={cn("flex items-center gap-2 min-w-0", className)}>
      <span
        className={cn("size-2 shrink-0 rounded-full", runDotColor(status))}
        aria-hidden
      />
      <Link href={appPath(href)} className="truncate text-link font-medium hover:underline">
        {name}
      </Link>
    </div>
  )
}

export function RegistryLink({
  href,
  children,
  className,
}: {
  href: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <Link href={appPath(href)} className={cn("text-link hover:underline", className)}>
      {children}
    </Link>
  )
}
