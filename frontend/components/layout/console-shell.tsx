"use client"

import { AppShell } from "@/components/layout/app-shell"
import { OpsContextBar } from "@/components/console/ops-context-bar"
import { consoleBrand, consoleNavGroups } from "@/lib/constants/console-navigation"

export function ConsoleShell({ children }: { children: React.ReactNode }) {
  return (
    <AppShell
      navGroups={consoleNavGroups}
      brand={consoleBrand}
      headerExtra={<OpsContextBar />}
      footer={
        <p className="text-[10px] leading-relaxed text-muted-foreground">
          ABSA Studio · local control plane
        </p>
      }
    >
      {children}
    </AppShell>
  )
}
