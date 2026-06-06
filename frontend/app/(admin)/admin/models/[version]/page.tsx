import { ModelDetailPageClient } from "./model-detail-client"

type PageProps = {
  params: Promise<{ version: string }>
}

export function generateStaticParams() {
  return [{ version: "absa-v1" }]
}

export default async function ModelDetailPage({ params }: PageProps) {
  const { version } = await params
  return <ModelDetailPageClient version={version} />
}
