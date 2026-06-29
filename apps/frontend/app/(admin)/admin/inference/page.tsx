import { InferencePlayground } from "@/components/admin/inference-playground"

export const metadata = { title: "Inference" }

export default function InferencePage() {
  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-[15px] font-semibold tracking-tight">Inference</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Manual test against the production model — spans, confidence, and guardrails
        </p>
      </header>
      <InferencePlayground />
    </div>
  )
}
