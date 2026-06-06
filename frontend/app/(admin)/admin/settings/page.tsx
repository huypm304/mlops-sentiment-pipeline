"use client"

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

import { EmptyState } from "@/components/ui/empty-state"
import { fetchPlatformSettings, type PlatformSettings } from "@/lib/api/analytics"

export default function SettingsPage() {
  const [settings, setSettings] = useState<PlatformSettings | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPlatformSettings()
      .then(setSettings)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load settings"),
      )
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading settings…
      </div>
    )
  }

  if (error || !settings) {
    return <EmptyState title="Settings unavailable" description={error ?? undefined} />
  }

  const sections = [
    {
      title: "Platform",
      items: [
        { label: "Environment", value: settings.environment },
        { label: "Production model", value: settings.production_model },
        { label: "Model directory", value: settings.model_dir },
        { label: "Endpoint status", value: settings.endpoint_status },
        { label: "Artifacts bucket", value: settings.artifacts_bucket ?? "—" },
      ],
    },
    {
      title: "Inference guardrails",
      items: settings.guardrails
        ? [
            { label: "Reject (global)", value: `${Math.round(settings.guardrails.reject_global * 100)}%` },
            { label: "Review (global)", value: `${Math.round(settings.guardrails.review_global * 100)}%` },
            { label: "Warn (global)", value: `${Math.round(settings.guardrails.warn_global * 100)}%` },
            { label: "Aspect low", value: `${Math.round(settings.guardrails.aspect_low * 100)}%` },
            { label: "Review queue", value: "REVIEW + REJECT only" },
          ]
        : [{ label: "Guardrails", value: "defaults" }],
    },
    {
      title: "Monitoring",
      items: [
        { label: "Drift threshold", value: String(settings.drift_threshold) },
        { label: "Request volume", value: String(settings.request_volume_total) },
        { label: "Uptime (seconds)", value: String(settings.uptime_seconds) },
        { label: "Pipeline demo mode", value: settings.pipeline_demo_mode ? "enabled" : "disabled" },
        { label: "Retrain state machine", value: settings.retrain_state_machine ?? "—" },
      ],
    },
  ]

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-[15px] font-semibold tracking-tight">Settings</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Platform configuration from backend environment
        </p>
      </header>

      {sections.map((section) => (
        <div key={section.title} className="rounded-lg border border-border/60 bg-card">
          <div className="border-b border-border/60 px-4 py-2.5">
            <p className="text-[12px] font-medium uppercase tracking-wider text-muted-foreground">
              {section.title}
            </p>
          </div>
          <div className="divide-y divide-border/30">
            {section.items.map((item) => (
              <div
                key={item.label}
                className="flex items-center justify-between gap-3 px-4 py-2.5"
              >
                <span className="text-[13px]">{item.label}</span>
                <span className="max-w-[60%] truncate font-mono text-[12px] text-muted-foreground">
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
