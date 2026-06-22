export function formatRelativeTime(value: string | null | undefined): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "—"

  const diffMs = Date.now() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  if (diffSec < 60) return "just now"

  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin} minute${diffMin === 1 ? "" : "s"} ago`

  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour} hour${diffHour === 1 ? "" : "s"} ago`

  const diffDay = Math.floor(diffHour / 24)
  if (diffDay < 30) return `${diffDay} day${diffDay === 1 ? "" : "s"} ago`

  return formatShortDate(value)
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null || seconds <= 0) return "—"
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m`
  return `${seconds}s`
}

export function formatShortDate(value: string | null | undefined): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value.slice(0, 10)
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

export function formatF1(value: number | null | undefined): string {
  if (value == null || value <= 0) return "—"
  return value.toFixed(2)
}

export function datasetAuditLabel(status: string | undefined, auditPassed?: boolean): string {
  if (auditPassed || status === "pass") return "Pass"
  if (status === "running") return "Running"
  if (status === "fail") return "Fail"
  return "Pending"
}

export function runDotColor(status: string): string {
  const key = status.toLowerCase()
  if (key === "succeeded" || key === "success") return "bg-emerald-500"
  if (key === "running") return "bg-sky-500"
  if (key === "failed") return "bg-red-500"
  return "bg-muted-foreground/50"
}
