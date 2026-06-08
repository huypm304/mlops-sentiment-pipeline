import {
  Database,
  Gauge,
  Home,
  PlaySquare,
  Settings,
  Sparkles,
  Workflow,
} from "lucide-react"

import type { NavGroup } from "@/types/navigation"

export const consoleNavGroups: NavGroup[] = [
  {
    title: "Workspace",
    items: [
      { title: "Home", href: "/", icon: Home },
      { title: "Datasets", href: "/datasets", icon: Database },
      { title: "Training Runs", href: "/training-runs", icon: Workflow },
      { title: "Models", href: "/models", icon: PlaySquare },
      { title: "Inference", href: "/inference", icon: Sparkles },
      { title: "Monitoring", href: "/monitoring", icon: Gauge },
      { title: "Settings", href: "/settings", icon: Settings },
    ],
  },
]
