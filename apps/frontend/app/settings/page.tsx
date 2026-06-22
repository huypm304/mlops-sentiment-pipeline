"use client"

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

import { ConsoleShell } from "@/components/layout/console-shell"
import { SectionHeader } from "@/components/console/section-header"
import { fetchPlatformSettings, type PlatformSettings } from "@/lib/api/analytics"

export default function SettingsPage() {
  const [settings, setSettings] = useState<PlatformSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPlatformSettings()
      .then(setSettings)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load settings"))
      .finally(() => setLoading(false))
  }, [])

  return (
    <ConsoleShell>
      <section className="space-y-4">
        <SectionHeader title="Settings" description="Operational configuration." />

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading settings
          </div>
        ) : error ? (
          <p className="text-sm text-red-500">{error}</p>
        ) : !settings ? (
          <p className="text-sm text-muted-foreground">No settings available.</p>
        ) : (
          <div className="rounded-md border border-border bg-card">
            <div className="divide-y divide-border/70 text-sm">
              <SettingRow label="Environment" value={settings.environment} />
              <SettingRow label="Production model" value={settings.production_model} />
              <SettingRow label="Endpoint" value={settings.endpoint_status} />
              <SettingRow label="Artifacts bucket" value={settings.artifacts_bucket ?? "-"} />
              <SettingRow label="Drift threshold" value={String(settings.drift_threshold)} />
              <SettingRow label="Request volume" value={String(settings.request_volume_total)} />
            </div>
          </div>
        )}
      </section>
    </ConsoleShell>
  )
}

function SettingRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 px-4 py-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono text-xs">{value}</span>
    </div>
  )
}
