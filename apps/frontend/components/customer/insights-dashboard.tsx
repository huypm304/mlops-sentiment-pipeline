"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { AlertCircle, FileText, Loader2, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import {
  fetchWeeklyReport,
  fetchWeeklyReports,
  triggerWeeklyReport,
} from "@/lib/api/reports"
import type { WeeklyReport, WeeklyReportSummary } from "@/types/weekly-report"
import { cn } from "@/lib/utils"

const SENTIMENT_LABELS: Record<string, string> = {
  positive: "Tích cực",
  negative: "Tiêu cực",
  neutral: "Trung tính",
}

const INSIGHT_STYLES: Record<string, string> = {
  warning: "border-amber-500/25 bg-amber-500/5 text-amber-200",
  positive: "border-emerald-500/25 bg-emerald-500/5 text-emerald-200",
  quality: "border-red-500/25 bg-red-500/5 text-red-200",
  keywords: "border-blue-500/25 bg-blue-500/5 text-blue-200",
  summary: "border-border/60 bg-muted/20 text-foreground",
  info: "border-border/60 bg-muted/10 text-muted-foreground",
}

function formatPeriod(start?: string, end?: string) {
  if (!start || !end) return "—"
  return `${start.slice(0, 10)} → ${end.slice(0, 10)}`
}

function pct(value: number) {
  return `${(value * 100).toFixed(1)}%`
}

export function InsightsDashboard() {
  const [reports, setReports] = useState<WeeklyReportSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<WeeklyReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadReports = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const payload = await fetchWeeklyReports()
      const rows = payload.reports ?? []
      setReports(rows)
      if (rows.length > 0) {
        setSelectedId((current) => current ?? rows[0].report_id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không tải được danh sách báo cáo")
      setReports([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadReports()
  }, [loadReports])

  useEffect(() => {
    if (!selectedId) {
      setDetail(null)
      return
    }
    setDetailLoading(true)
    fetchWeeklyReport(selectedId)
      .then(setDetail)
      .catch(() => setDetail(null))
      .finally(() => setDetailLoading(false))
  }, [selectedId])

  async function handleGenerate() {
    setGenerating(true)
    setError(null)
    try {
      const result = await triggerWeeklyReport({ periodDays: 7 })
      await loadReports()
      if (result.report?.report_id) {
        setSelectedId(result.report.report_id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không tạo được báo cáo")
    } finally {
      setGenerating(false)
    }
  }

  const stats = detail?.stats
  const aspectRows = useMemo(() => {
    if (!stats) return []
    return Object.keys(stats.aspect_share ?? {})
      .map((aspect) => ({
        aspect,
        share: stats.aspect_share[aspect] ?? 0,
        counts: stats.aspect_sentiment?.[aspect] ?? {},
        rates: stats.aspect_sentiment_rates?.[aspect] ?? {},
      }))
      .sort((a, b) => b.share - a.share)
  }, [stats])

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Business insights</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Báo cáo tuần tổng hợp review production — sentiment, khía cạnh, từ khóa, nhận định.
          </p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={loadReports} disabled={loading}>
            <RefreshCw className={cn("mr-1.5 size-3.5", loading && "animate-spin")} />
            Làm mới
          </Button>
          <Button size="sm" onClick={handleGenerate} disabled={generating}>
            {generating ? (
              <>
                <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                Đang tạo…
              </>
            ) : (
              "Tạo báo cáo ngay"
            )}
          </Button>
        </div>
      </header>

      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {loading ? (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Đang tải báo cáo…
        </div>
      ) : reports.length === 0 ? (
        <EmptyState
          title="Chưa có báo cáo tuần"
          description="Chạy inference để thu thập review, sau đó bấm “Tạo báo cáo ngay”."
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
          <aside className="rounded-lg border border-border/60 bg-card p-2">
            <p className="px-2 py-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              Các kỳ báo cáo
            </p>
            <div className="space-y-1">
              {reports.map((row) => (
                <button
                  key={row.report_id}
                  type="button"
                  onClick={() => setSelectedId(row.report_id)}
                  className={cn(
                    "w-full rounded-md px-2 py-2 text-left text-sm transition-colors",
                    selectedId === row.report_id
                      ? "bg-primary/10 text-foreground"
                      : "hover:bg-muted/40 text-muted-foreground",
                  )}
                >
                  <p className="font-medium">{row.name}</p>
                  <p className="mt-0.5 text-[11px]">
                    {formatPeriod(row.period_start, row.period_end)} · {row.total_reviews} review
                  </p>
                </button>
              ))}
            </div>
          </aside>

          <div className="space-y-4">
            {detailLoading || !detail ? (
              <div className="flex items-center gap-2 rounded-lg border border-dashed border-border/60 px-4 py-10 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                Đang tải chi tiết báo cáo…
              </div>
            ) : (
              <>
                <div className="grid gap-3 sm:grid-cols-4">
                  {(["positive", "negative", "neutral"] as const).map((key) => (
                    <div key={key} className="rounded-lg border border-border/60 bg-card p-4">
                      <p className="text-[11px] text-muted-foreground">{SENTIMENT_LABELS[key]}</p>
                      <p className="mt-1 text-2xl font-semibold tabular-nums">
                        {pct(detail.stats.sentiment_mix[key] ?? 0)}
                      </p>
                    </div>
                  ))}
                  <div className="rounded-lg border border-border/60 bg-card p-4">
                    <p className="text-[11px] text-muted-foreground">Tổng review</p>
                    <p className="mt-1 text-2xl font-semibold tabular-nums">
                      {detail.stats.total_reviews}
                    </p>
                  </div>
                </div>

                <div className="rounded-lg border border-border/60 bg-card">
                  <div className="border-b border-border/40 px-4 py-2.5">
                    <p className="text-[12px] font-medium">Nhận định cho doanh nghiệp</p>
                  </div>
                  <div className="space-y-2 p-4">
                    {(detail.insights ?? []).map((item, idx) => (
                      <div
                        key={idx}
                        className={cn(
                          "rounded-md border px-3 py-2 text-sm",
                          INSIGHT_STYLES[item.type] ?? INSIGHT_STYLES.info,
                        )}
                      >
                        {item.message.replace(/\*\*(.*?)\*\*/g, "$1")}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="rounded-lg border border-border/60 bg-card">
                    <div className="border-b border-border/40 px-4 py-2.5">
                      <p className="text-[12px] font-medium">Khía cạnh × sentiment</p>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-border/30 text-[11px] text-muted-foreground">
                            <th className="px-4 py-2 text-left font-medium">Aspect</th>
                            <th className="px-4 py-2 text-right font-medium">Share</th>
                            <th className="px-4 py-2 text-right font-medium">Neg</th>
                            <th className="px-4 py-2 text-right font-medium">Pos</th>
                          </tr>
                        </thead>
                        <tbody>
                          {aspectRows.map((row) => (
                            <tr key={row.aspect} className="border-b border-border/20 last:border-0">
                              <td className="px-4 py-2">{row.aspect}</td>
                              <td className="px-4 py-2 text-right tabular-nums">{pct(row.share)}</td>
                              <td className="px-4 py-2 text-right tabular-nums text-red-400">
                                {pct(row.rates.negative ?? 0)}
                              </td>
                              <td className="px-4 py-2 text-right tabular-nums text-emerald-400">
                                {pct(row.rates.positive ?? 0)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="rounded-lg border border-border/60 bg-card">
                    <div className="border-b border-border/40 px-4 py-2.5">
                      <p className="text-[12px] font-medium">Top keywords</p>
                    </div>
                    <div className="grid gap-4 p-4 sm:grid-cols-2">
                      <KeywordList
                        title="Tiêu cực"
                        items={detail.stats.top_keywords.negative}
                      />
                      <KeywordList
                        title="Tích cực"
                        items={detail.stats.top_keywords.positive}
                      />
                    </div>
                  </div>
                </div>

                {detail.s3_markdown_uri && (
                  <div className="flex items-center gap-2 text-[12px] text-muted-foreground">
                    <FileText className="size-3.5" />
                    <span>Markdown: {detail.s3_markdown_uri}</span>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function KeywordList({
  title,
  items,
}: {
  title: string
  items: { keyword: string; count: number }[]
}) {
  if (!items?.length) {
    return (
      <div>
        <p className="mb-2 text-[11px] font-medium text-muted-foreground">{title}</p>
        <p className="text-sm text-muted-foreground/60">Không có dữ liệu</p>
      </div>
    )
  }
  return (
    <div>
      <p className="mb-2 text-[11px] font-medium text-muted-foreground">{title}</p>
      <ul className="space-y-1">
        {items.map((item) => (
          <li key={item.keyword} className="flex justify-between text-sm">
            <span>{item.keyword}</span>
            <span className="font-mono text-[12px] tabular-nums text-muted-foreground">
              {item.count}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
