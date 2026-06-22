"use client"

import { useEffect, useState } from "react"

import { AppShell } from "@/components/layout/app-shell"
import {
  adminNavGroups,
  defaultAdminRoute,
} from "@/lib/constants/admin-navigation"
import { fetchModels } from "@/lib/api/metrics"
import { fetchHealth } from "@/lib/api/runtime"
import { cn } from "@/lib/utils"

function EndpointDot({ status }: { status: "ready" | "disabled" | "degraded" }) {
  return (
    <span
      className={cn(
        "inline-block size-1.5 rounded-full",
        status === "ready" && "bg-emerald-500",
        status === "degraded" && "bg-amber-500",
        status === "disabled" && "bg-muted-foreground/40",
      )}
    />
  )
}

export function AdminShell({ children }: { children: React.ReactNode }) {
  const [prodVersion, setProdVersion] = useState<string | null>(null)
  const [endpointStatus, setEndpointStatus] = useState<"ready" | "disabled" | "degraded">("disabled")

  useEffect(() => {
    fetchModels()
      .then((models) => {
        const prod = models.find((m) => m.status === "production")
        setProdVersion(prod?.version ?? models[0]?.version ?? null)
      })
      .catch(() => setProdVersion(null))

    fetchHealth()
      .then((h) => {
        setEndpointStatus(h.endpoint_health === "healthy" ? "ready" : "degraded")
      })
      .catch(() => setEndpointStatus("disabled"))
  }, [])

  return (
    <AppShell
      navGroups={adminNavGroups}
      brand={{
        title: "ABSA MLOps",
        subtitle: "Control plane",
        href: defaultAdminRoute,
      }}
      headerExtra={
        <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <span className="text-muted-foreground/60">ENV</span>
            <span className="font-medium text-foreground">demo</span>
          </span>
          <span className="text-border">|</span>
          <span className="flex items-center gap-1">
            <span className="text-muted-foreground/60">MODEL</span>
            <span className="font-mono font-medium text-foreground">
              {prodVersion ?? "—"}
            </span>
          </span>
          <span className="text-border">|</span>
          <span className="flex items-center gap-1.5">
            <EndpointDot status={endpointStatus} />
            <span className="capitalize">{endpointStatus}</span>
          </span>
        </div>
      }
      footer={
        <p className="text-[10px] text-muted-foreground/60">
          Vietnamese ABSA · MLOps Platform
        </p>
      }
      switchLink={{ href: "/reviews", label: "Customer view" }}
    >
      {children}
    </AppShell>
  )
}
