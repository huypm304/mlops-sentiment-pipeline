import { EmptyState } from "@/components/ui/empty-state"

export const metadata = { title: "Audit" }

export default function AuditPage() {
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold tracking-tight">Dataset audit</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Quality checks before training
        </p>
      </header>
      <EmptyState
        title="No audit reports"
        description="Dataset audit results will appear after running the data quality pipeline."
      />
    </div>
  )
}
