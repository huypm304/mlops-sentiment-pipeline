export type WeeklyReportInsight = {
  type: string
  message: string
}

export type WeeklyKeyword = {
  keyword: string
  count: number
  share_pct: number
}

export type WeeklyReportStats = {
  total_reviews: number
  sentiment_mix: Record<string, number>
  sentiment_counts: Record<string, number>
  aspect_share: Record<string, number>
  aspect_counts: Record<string, number>
  aspect_sentiment: Record<string, Record<string, number>>
  aspect_sentiment_rates: Record<string, Record<string, number>>
  low_confidence_rate: number
  no_opinion_rate: number
  top_keywords: {
    overall: WeeklyKeyword[]
    negative: WeeklyKeyword[]
    positive: WeeklyKeyword[]
  }
}

export type WeeklyReportSummary = {
  report_id: string
  name: string
  model_id: string
  period_start: string
  period_end: string
  total_reviews: number
  created_at?: string
  s3_markdown_uri?: string
}

export type WeeklyReport = WeeklyReportSummary & {
  period_days?: number
  stats: WeeklyReportStats
  insights: WeeklyReportInsight[]
  previous_report_id?: string
  s3_json_key?: string
  s3_markdown_key?: string
  s3_json_uri?: string
}

export type WeeklyReportsListResponse = {
  reports: WeeklyReportSummary[]
}
