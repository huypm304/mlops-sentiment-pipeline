import { EmptyState } from "@/components/ui/empty-state"

export const metadata = { title: "Pipeline" }

export default function PipelinePage() {
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold tracking-tight">Retraining pipeline</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Step Functions workflow for dataset audit through deployment
        </p>
      </header>
      <EmptyState
        title="No pipeline runs"
        description="Pipeline status will appear when a retraining job is triggered via Step Functions."
      />
    </div>
  )
}
