import { DatasetDetailClient } from "./dataset-detail-client"

type PageProps = {
  params: Promise<{ datasetId: string }>
}

export function generateStaticParams() {
  return [{ datasetId: "sample-dataset" }]
}

export default async function DatasetDetailPage({ params }: PageProps) {
  const { datasetId } = await params
  return <DatasetDetailClient datasetId={decodeURIComponent(datasetId)} />
}
