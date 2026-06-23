"use client"

import { Loader2 } from "lucide-react"

import { cn } from "@/lib/utils"
import type { PipelineStage, SfnStep } from "@/types/pipeline"

type Props = {
  steps: SfnStep[] | PipelineStage[]
  currentState?: string | null
  compact?: boolean
}

export const ACTIVE_RUN_STATUSES = new Set([
  "RUNNING",
  "TRAINING",
  "TRAINING_IN_PROGRESS",
  "TRAINING_COMPLETED",
  "EVALUATED",
  "COMPARED",
])

export function isActiveRunStatus(status: string) {
  return ACTIVE_RUN_STATUSES.has(status.toUpperCase())
}

export function PipelineStageStepper({ steps, currentState, compact }: Props) {
  if (steps.length === 0) return null

  return (
    <div className="space-y-2">
      {currentState ? (
        <p className="text-xs text-muted-foreground">
          Bước hiện tại:{" "}
          <span className="font-mono text-primary">{currentState}</span>
        </p>
      ) : null}
      <ol className={cn("flex flex-wrap gap-2", compact && "gap-1.5")}>
        {steps.map((step, idx) => {
          const status = step.status
          const name = step.name
          const key = "id" in step && step.id ? step.id : `${name}-${idx}`
          return (
            <li
              key={key}
              className={cn(
                "flex items-center gap-1 rounded-md border px-2 py-1 text-[11px] font-medium",
                status === "completed" && "border-chart-2/40 bg-chart-2/10 text-chart-2",
                status === "running" && "border-primary/50 bg-primary/10 text-primary",
                status === "failed" && "border-destructive/50 bg-destructive/10 text-destructive",
                status === "pending" && "border-border/60 text-muted-foreground",
                compact && "px-1.5 py-0.5 text-[10px]",
              )}
            >
              {status === "running" ? <Loader2 className="size-3 animate-spin" /> : null}
              {name}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
