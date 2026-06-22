import type { LucideIcon } from "lucide-react"

export type NavItem = {
  title: string
  href: string
  icon: LucideIcon
  description?: string
  badge?: string
}

export type NavGroup = {
  title: string
  items: NavItem[]
}
