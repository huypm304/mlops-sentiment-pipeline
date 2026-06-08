import { RunDetailClient } from "./run-detail-client"

type PageProps = {
  params: Promise<{ runId: string }>
}

export function generateStaticParams() {
  return [{ runId: "sample-run" }]
}

export default async function RunDetailPage({ params }: PageProps) {
  const { runId } = await params
  return <RunDetailClient runId={decodeURIComponent(runId)} />
}
