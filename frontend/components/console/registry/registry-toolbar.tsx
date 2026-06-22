"use client"

import { Search } from "lucide-react"

import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

export type ToolbarFilter = {
  label: string
  value: string
  options: { label: string; value: string }[]
  onChange: (value: string) => void
}

export function RegistryToolbar({
  search,
  onSearchChange,
  searchPlaceholder = "Search…",
  filters = [],
  actions,
  className,
}: {
  search?: string
  onSearchChange?: (value: string) => void
  searchPlaceholder?: string
  filters?: ToolbarFilter[]
  actions?: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn("registry-toolbar flex flex-wrap items-center gap-2 px-3 py-2", className)}>
      {onSearchChange != null ? (
        <label className="relative min-w-[200px] flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search ?? ""}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            className="h-8 pl-8"
          />
        </label>
      ) : null}

      {filters.map((filter) => (
        <label key={filter.label} className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
          <span className="whitespace-nowrap">{filter.label}</span>
          <select
            value={filter.value}
            onChange={(e) => filter.onChange(e.target.value)}
            className="h-8 rounded-sm border border-input bg-background px-2 text-[13px] text-foreground outline-none focus:border-ring focus:ring-1 focus:ring-ring"
          >
            {filter.options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      ))}

      {actions ? <div className="ml-auto flex shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
  )
}
