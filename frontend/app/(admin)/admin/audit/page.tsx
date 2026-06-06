import { AuditDashboard } from "@/components/admin/audit-dashboard"

export const metadata = { title: "Dataset audit" }

export default function AuditPage() {
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold tracking-tight">Dataset audit</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          VLSP-style quality checks and benchmarks before training
        </p>
      </header>
      <AuditDashboard />
    </div>
  )
}
