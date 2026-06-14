"use client"

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

import { ConsoleShell } from "@/components/layout/console-shell"
import {
  PlatformMetadataLine,
  RegistryPageHeader,
  RegistrySurface,
  RegistryTable,
  RegistryTd,
  RegistryTr,
} from "@/components/console/registry"
import { fetchPlatformSettings, type PlatformSettings } from "@/lib/api/analytics"
import { fetchMonitoring } from "@/lib/api/runtime"

function formatUptime(seconds: number) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

export default function CostPage() {
  const [platform, setPlatform] = useState<PlatformSettings | null>(null)
  const [runtime, setRuntime] = useState<Awaited<ReturnType<typeof fetchMonitoring>> | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([fetchPlatformSettings(), fetchMonitoring()])
      .then(([p, r]) => {
        setPlatform(p)
        setRuntime(r)
      })
      .catch((err) =>
        setNotice(err instanceof Error ? err.message : "Usage data unavailable"),
      )
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <ConsoleShell>
        <div className="flex items-center gap-2 py-8 text-[13px] text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Loading usage…
        </div>
      </ConsoleShell>
    )
  }

  const metaLine =
    platform && runtime
      ? [
          `${runtime.request_volume_total.toLocaleString()} requests`,
          `Avg ${runtime.avg_latency_ms} ms`,
          `Uptime ${formatUptime(platform.uptime_seconds)}`,
          `Error rate ${runtime.error_rate_pct}%`,
        ].join(" · ")
      : null

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <RegistryPageHeader
          title="Cost & Usage"
          metadata={
            <>
              <PlatformMetadataLine />
              {metaLine ? <p className="mt-0.5">{metaLine}</p> : null}
            </>
          }
        />

        {platform && runtime ? (
          <RegistrySurface notice={notice}>
            <RegistryTable>
              <tbody>
                <UsageRow label="Environment" value={platform.environment} />
                <UsageRow label="Production model" value={platform.production_model} />
                <UsageRow label="Model directory" value={platform.model_dir} />
                <UsageRow label="Endpoint status" value={platform.endpoint_status} />
                <UsageRow
                  label="Drift predictions logged"
                  value={String(
                    runtime.drift?.production_sample_size ??
                      runtime.drift?.production?.sample_size ??
                      0,
                  )}
                />
                <UsageRow label="Pipeline demo mode" value={platform.pipeline_demo_mode ? "enabled" : "disabled"} />
                <UsageRow label="Artifacts bucket" value={platform.artifacts_bucket ?? "not configured"} />
              </tbody>
            </RegistryTable>
          </RegistrySurface>
        ) : (
          <RegistrySurface notice={notice ?? "Usage data unavailable"}>
            <div />
          </RegistrySurface>
        )}
      </section>
    </ConsoleShell>
  )
}

function UsageRow({ label, value }: { label: string; value: string }) {
  return (
    <RegistryTr>
      <RegistryTd>{label}</RegistryTd>
      <RegistryTd align="right" mono muted>
        {value}
      </RegistryTd>
    </RegistryTr>
  )
}
