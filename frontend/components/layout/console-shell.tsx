"use client"

import { AppShell } from "@/components/layout/app-shell"
import { consoleNavGroups } from "@/lib/constants/console-navigation"

export function ConsoleShell({ children }: { children: React.ReactNode }) {
  return (
    <AppShell
      navGroups={consoleNavGroups}
      brand={{
        title: "ML Platform",
        subtitle: "Operations",
        href: "/",
      }}
      headerExtra={
        <p className="text-xs text-muted-foreground">
          Dataset registry · training runs · model registry
        </p>
      }
      footer={<p className="text-[11px] text-muted-foreground">ABSA control plane</p>}
    >
      {children}
    </AppShell>
  )
}
