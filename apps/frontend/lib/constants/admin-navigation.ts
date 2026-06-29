import {
  Activity,
  CircleDollarSign,
  Database,
  GitBranch,
  Inbox,
  LayoutDashboard,
  Settings,
  Terminal,
  Workflow,
} from "lucide-react"

import type { NavGroup } from "@/types/navigation"

export const adminNavGroups: NavGroup[] = [
  {
    title: "Overview",
    items: [
      {
        title: "Dashboard",
        href: "/admin/dashboard",
        icon: LayoutDashboard,
        description: "Operational overview",
      },
    ],
  },
  {
    title: "Data",
    items: [
      {
        title: "Datasets",
        href: "/admin/datasets",
        icon: Database,
        description: "Dataset registry and uploads",
      },
    ],
  },
  {
    title: "Model",
    items: [
      {
        title: "Training Runs",
        href: "/admin/pipeline",
        icon: Workflow,
        description: "Retraining pipeline",
      },
      {
        title: "Model Registry",
        href: "/admin/models",
        icon: GitBranch,
        description: "Production and candidate models",
      },
    ],
  },
  {
    title: "Operations",
    items: [
      {
        title: "Inference",
        href: "/admin/inference",
        icon: Terminal,
        description: "Inference playground",
      },
      {
        title: "Monitoring",
        href: "/admin/monitoring",
        icon: Activity,
        description: "API health and review signals",
      },
      {
        title: "Review Queue",
        href: "/admin/review-queue",
        icon: Inbox,
        description: "Low-confidence prediction review",
      },
      {
        title: "Cost & Usage",
        href: "/admin/cost",
        icon: CircleDollarSign,
        description: "Resource cost estimates",
      },
    ],
  },
  {
    title: "System",
    items: [
      {
        title: "Settings",
        href: "/admin/settings",
        icon: Settings,
        description: "Platform configuration",
      },
    ],
  },
]

export const defaultAdminRoute = "/admin/dashboard" as const

/** Routes kept in codebase but hidden from sidebar navigation. */
export const adminHiddenRoutes = [
  "/admin/audit",
  "/admin/analytics",
  "/admin/compare",
  "/admin/evaluation",
] as const
