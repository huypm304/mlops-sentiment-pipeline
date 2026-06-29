"use client"

import { Cpu, FlaskConical } from "lucide-react"

import type { PipelineConfig } from "@/types/pipeline"
import { cn } from "@/lib/utils"

type Props = {
  config: PipelineConfig | null
  className?: string
}

export function TrainingModeBanner({ config, className }: Props) {
  if (!config?.configured) return null

  const real = config.sagemaker_training_enabled ?? config.training_mode === "sagemaker"

  if (real) {
    return (
      <div
        className={cn(
          "flex gap-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm",
          className,
        )}
      >
        <Cpu className="mt-0.5 size-4 shrink-0 text-emerald-500" />
        <div className="text-muted-foreground">
          <p className="font-medium text-foreground">SageMaker GPU training</p>
          <p>
            Mỗi run sẽ train thật 50 epoch trên GPU (<code className="text-xs">train_kaggle.py</code>), tạo{" "}
            <code className="text-xs">best_model.pt</code> + <code className="text-xs">train_log.csv</code>. Cần{" "}
            <code className="text-xs">train.jsonl</code> và <code className="text-xs">dev.jsonl</code> trên S3.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "flex gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm",
        className,
      )}
    >
      <FlaskConical className="mt-0.5 size-4 shrink-0 text-amber-500" />
      <div className="text-muted-foreground">
        <p className="font-medium text-foreground">Mock training (giả lập)</p>
        <p>
          Backend đang copy artifact production — không train model mới. Deploy Runtime với{" "}
          <strong className="font-medium text-foreground">enable_sagemaker_training = true</strong> để train thật.
        </p>
      </div>
    </div>
  )
}
