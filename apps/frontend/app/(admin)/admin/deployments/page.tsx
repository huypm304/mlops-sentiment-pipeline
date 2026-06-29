import { EmptyState } from "@/components/ui/empty-state"

export const metadata = { title: "Deployments" }

export default function DeploymentsPage() {
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold tracking-tight">Deployment history</h1>
        <p className="mt-1 text-sm text-muted-foreground">Production releases</p>
      </header>
      <EmptyState
        title="No deployments"
        description="Deployment history will appear when models are promoted to production."
      />
    </div>
  )
}
