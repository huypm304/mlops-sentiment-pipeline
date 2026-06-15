import { Suspense } from "react"
import { Loader2 } from "lucide-react"

import { AuditDashboard } from "@/components/admin/audit-dashboard"

export const metadata = { title: "Dataset audit" }

export default function AuditPage() {
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold tracking-tight">Dataset audit</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          VLSP-style quality checks and benchmarks on uploaded train / dev / test splits
        </p>
      </header>
      <Suspense
        fallback={
          <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading…
          </div>
        }
      >
        <AuditDashboard />
      </Suspense>
    </div>
  )
}
