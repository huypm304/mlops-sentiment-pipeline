import { EmptyState } from "@/components/ui/empty-state"

export function ModelComparison() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold tracking-tight">Model comparison</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Compare evaluation reports between two registered versions
        </p>
      </header>
      <EmptyState
        title="No comparison data"
        description="Select two model versions from the registry once evaluation reports are available."
      />
    </div>
  )
}
