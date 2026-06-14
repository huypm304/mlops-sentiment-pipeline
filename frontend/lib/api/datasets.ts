import type {
  DatasetAuditResponse,
  DatasetListItem,
  DatasetManifest,
} from "@/types/dataset"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? ""

async function fetchOrThrow(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init)
  } catch (err) {
    const target = typeof input === "string" ? input : input.toString()
    const hint = target.includes("amazonaws.com")
      ? "S3 upload blocked — artifact bucket CORS must allow this site origin."
      : "Check NEXT_PUBLIC_API_URL and API CORS (api.minhhuy.me)."
    throw new Error(
      `Network error calling ${target.split("?")[0]}: ${err instanceof Error ? err.message : "fetch failed"}. ${hint}`,
    )
  }
}

function assertJson(res: Response): void {
  const ct = res.headers.get("content-type") ?? ""
  if (!ct.includes("json")) {
    throw new Error(
      API_BASE
        ? `Server returned non-JSON response (${res.status})`
        : "API not configured – set NEXT_PUBLIC_API_URL"
    )
  }
}

function usePresignUpload(): boolean {
  if (process.env.NEXT_PUBLIC_USE_PRESIGN_UPLOAD === "true") return true
  return API_BASE.startsWith("https://") && !API_BASE.includes("localhost")
}

async function parseError(res: Response): Promise<string> {
  let detail = res.statusText
  try {
    const body = (await res.json()) as { detail?: string | { msg?: string }[] }
    if (typeof body.detail === "string") detail = body.detail
    else if (Array.isArray(body.detail) && body.detail[0]?.msg)
      detail = body.detail[0].msg
  } catch {
    /* ignore */
  }
  return detail || `API error: ${res.status}`
}

export async function fetchDatasets(): Promise<DatasetListItem[]> {
  if (!API_BASE) throw new Error("API not configured – set NEXT_PUBLIC_API_URL")
  const res = await fetchOrThrow(`${API_BASE}/datasets`)
  if (!res.ok) throw new Error(await parseError(res))
  assertJson(res)
  const data = (await res.json()) as { datasets: DatasetListItem[] }
  return data.datasets
}

export async function fetchDataset(datasetId: string): Promise<DatasetManifest> {
  if (!API_BASE) throw new Error("API not configured – set NEXT_PUBLIC_API_URL")
  const res = await fetchOrThrow(`${API_BASE}/datasets/${encodeURIComponent(datasetId)}`)
  if (!res.ok) throw new Error(await parseError(res))
  assertJson(res)
  return res.json() as Promise<DatasetManifest>
}

async function uploadViaPresign(input: {
  name: string
  train: File
  dev: File
  test?: File | null
}): Promise<DatasetManifest> {
  const res = await fetchOrThrow(`${API_BASE}/datasets/presign-upload`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: input.name, uploaded_by: "admin-ui" }),
  })
  if (!res.ok) throw new Error(await parseError(res))

  const payload = (await res.json()) as {
    dataset_id: string
    prefix: string
    upload_urls: Record<string, string>
  }

  const uploads: Array<[string, File]> = [
    ["train", input.train],
    ["dev", input.dev],
  ]
  if (input.test) uploads.push(["test", input.test])

  for (const [split, file] of uploads) {
    const url = payload.upload_urls[split]
    if (!url) throw new Error(`Missing presigned URL for split '${split}'`)
    const putRes = await fetchOrThrow(url, {
      method: "PUT",
      body: file,
      headers: { "Content-Type": "application/x-ndjson" },
    })
    if (!putRes.ok) throw new Error(`S3 upload failed for ${split}: ${putRes.statusText}`)
  }

  const now = new Date().toISOString()
  return {
    dataset_id: payload.dataset_id,
    name: input.name,
    status: "pending",
    created_at: now,
    updated_at: now,
    splits: Object.fromEntries(
      uploads.map(([split, file]) => [
        split,
        { filename: `${split}.jsonl`, rows: 0, size_bytes: file.size },
      ])
    ),
    audits: {},
    audit_passed: false,
  }
}

export async function uploadDatasetBundle(input: {
  name: string
  train: File
  dev: File
  test?: File | null
}): Promise<DatasetManifest> {
  if (usePresignUpload()) {
    return uploadViaPresign(input)
  }

  const form = new FormData()
  form.append("name", input.name)
  form.append("train", input.train)
  form.append("dev", input.dev)
  if (input.test) form.append("test", input.test)

  const res = await fetchOrThrow(`${API_BASE}/datasets/upload`, {
    method: "POST",
    body: form,
  })
  if (!res.ok) throw new Error(await parseError(res))
  const data = (await res.json()) as { dataset: DatasetManifest }
  return data.dataset
}

export async function auditDataset(datasetId: string): Promise<DatasetAuditResponse> {
  const res = await fetchOrThrow(`${API_BASE}/datasets/${encodeURIComponent(datasetId)}/audit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json() as Promise<DatasetAuditResponse>
}
