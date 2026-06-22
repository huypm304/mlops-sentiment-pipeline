import { BarChart3, MessageSquareText } from "lucide-react"

import type { NavGroup } from "@/types/navigation"

export const customerNavGroups: NavGroup[] = [
  {
    title: "Product",
    items: [
      {
        title: "Reviews",
        href: "/reviews",
        icon: MessageSquareText,
        description: "Analyze customer feedback",
      },
      {
        title: "Insights",
        href: "/insights",
        icon: BarChart3,
        description: "Business trends and complaints",
      },
    ],
  },
]

export const defaultCustomerRoute = "/reviews" as const
