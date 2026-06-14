import type { ReactNode } from "react"

export interface TableCardProps {
  title?: string
  action?: ReactNode
  toolbar?: ReactNode
  loading?: boolean
  loadingLabel?: string
  notice?: string | null
  noticeTone?: "warn" | "error" | "info"
  empty?: boolean
  emptyLabel?: string
  className?: string
  children?: ReactNode
}
