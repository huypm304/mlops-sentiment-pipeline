"use client"

import { AppShell } from "@/components/layout/app-shell"
import {
  customerNavGroups,
  defaultCustomerRoute,
} from "@/lib/constants/customer-navigation"

export function CustomerShell({ children }: { children: React.ReactNode }) {
  return (
    <AppShell
      navGroups={customerNavGroups}
      brand={{
        title: "Sentiment",
        subtitle: "Customer insights",
        href: defaultCustomerRoute,
      }}
      switchLink={{ href: "/admin/monitoring", label: "Admin console" }}
    >
      {children}
    </AppShell>
  )
}
