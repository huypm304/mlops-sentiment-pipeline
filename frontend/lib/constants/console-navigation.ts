import {
  Activity,
  Box,
  Database,
  DollarSign,
  Home,
  Inbox,
  Play,
  Settings,
  Workflow,
} from "lucide-react"

import type { NavGroup } from "@/types/navigation"

export const consoleNavGroups: NavGroup[] = [
  {
    title: "Platform",
    items: [{ title: "Overview", href: "/", icon: Home }],
  },
  {
    title: "Data",
    items: [{ title: "Datasets", href: "/datasets", icon: Database }],
  },
  {
    title: "Training",
    items: [{ title: "Training Runs", href: "/training-runs", icon: Workflow }],
  },
  {
    title: "Registry",
    items: [{ title: "Model Registry", href: "/models", icon: Box }],
  },
  {
    title: "Serving",
    items: [{ title: "Inference", href: "/inference", icon: Play }],
  },
  {
    title: "Operations",
    items: [
      { title: "Monitoring", href: "/monitoring", icon: Activity },
      { title: "Review Queue", href: "/review-queue", icon: Inbox },
    ],
  },
  {
    title: "System",
    items: [
      { title: "Cost & Usage", href: "/cost", icon: DollarSign },
      { title: "Settings", href: "/settings", icon: Settings },
    ],
  },
]

export const consoleBrand = {
  title: "ABSA Studio",
  href: "/",
} as const
