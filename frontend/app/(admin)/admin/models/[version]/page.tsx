import { ModelDetail } from "@/components/admin/model-detail"

type PageProps = {
  params: Promise<{ version: string }>
}

export async function generateMetadata({ params }: PageProps) {
  const { version } = await params
  return { title: `Model ${version}` }
}

export default async function ModelDetailPage({ params }: PageProps) {
  const { version } = await params
  return <ModelDetail version={version} />
}
