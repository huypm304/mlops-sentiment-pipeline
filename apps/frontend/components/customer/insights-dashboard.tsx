import { EmptyState } from "@/components/ui/empty-state"

export function InsightsDashboard() {
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold tracking-tight">Business insights</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Aggregated analytics from production reviews
        </p>
      </header>
      <EmptyState
        title="No analytics data"
        description="Insights will appear when review data is collected from the inference API and stored in the database."
      />
    </div>
  )
}
