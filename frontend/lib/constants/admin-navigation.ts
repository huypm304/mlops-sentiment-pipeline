import {
  Activity,
  BarChart3,
  FileSearch,
  GitCompare,
  GitBranch,
  History,
  Workflow,
} from "lucide-react"

import type { NavGroup } from "@/types/navigation"

export const adminNavGroups: NavGroup[] = [
  {
    title: "Operations",
    items: [
      {
        title: "Monitoring",
        href: "/admin/monitoring",
        icon: Activity,
        description: "API health, latency, errors",
      },
      {
        title: "Pipeline",
        href: "/admin/pipeline",
        icon: Workflow,
        description: "Retraining workflow",
      },
      {
        title: "Deployments",
        href: "/admin/deployments",
        icon: History,
        description: "Release history",
      },
    ],
  },
  {
    title: "Models",
    items: [
      {
        title: "Registry",
        href: "/admin/models",
        icon: GitBranch,
        description: "Registered model versions",
      },
      {
        title: "Compare",
        href: "/admin/compare",
        icon: GitCompare,
        description: "Version comparison",
      },
      {
        title: "Evaluation",
        href: "/admin/evaluation",
        icon: BarChart3,
        description: "Training & validation reports",
      },
    ],
  },
  {
    title: "Data",
    items: [
      {
        title: "Audit",
        href: "/admin/audit",
        icon: FileSearch,
        description: "Dataset quality reports",
      },
    ],
  },
]

export const defaultAdminRoute = "/admin/monitoring" as const
