"use client"

import { Input } from "@/components/ui/input"
import { TRAINING_CONFIG_FIELDS, type TrainingConfig, type TrainingConfigField } from "@/types/pipeline"

type Props = {
  value: TrainingConfig
  onChange: (key: TrainingConfigField, value: string) => void
  disabled?: boolean
  className?: string
}

export function TrainingConfigFields({ value, onChange, disabled, className }: Props) {
  return (
    <div className={className ?? "grid gap-3 sm:grid-cols-2"}>
      {TRAINING_CONFIG_FIELDS.map((key) => (
        <label key={key} className="text-xs">
          {key}
          <Input
            className="input-plain-number mt-1 font-mono text-xs"
            type="text"
            inputMode="decimal"
            autoComplete="off"
            value={value[key] != null ? String(value[key]) : ""}
            onChange={(e) => onChange(key, e.target.value)}
            disabled={disabled}
          />
        </label>
      ))}
    </div>
  )
}
