"use client"

import { InsightsDashboard } from "@/components/customer/insights-dashboard"
import { ConsoleShell } from "@/components/layout/console-shell"

export default function InsightsPage() {
  return (
    <ConsoleShell>
      <InsightsDashboard />
    </ConsoleShell>
  )
}
