"use client"

import { useEffect, useState } from "react"

import { AppShell } from "@/components/layout/app-shell"
import {
  adminNavGroups,
  defaultAdminRoute,
} from "@/lib/constants/admin-navigation"
import { fetchModels } from "@/lib/api/metrics"

export function AdminShell({ children }: { children: React.ReactNode }) {
  const [prodVersion, setProdVersion] = useState<string | null>(null)

  useEffect(() => {
    fetchModels()
      .then((models) => {
        const prod = models.find((m) => m.status === "production")
        setProdVersion(prod?.version ?? models[0]?.version ?? null)
      })
      .catch(() => setProdVersion(null))
  }, [])

  return (
    <AppShell
      navGroups={adminNavGroups}
      brand={{
        title: "ABSA Ops",
        subtitle: "MLOps console",
        href: defaultAdminRoute,
      }}
      footer={
        <span className="text-muted-foreground">
          {prodVersion ? `Prod · ${prodVersion}` : "Metrics API"}
        </span>
      }
      switchLink={{ href: "/reviews", label: "Customer app" }}
    >
      {children}
    </AppShell>
  )
}
