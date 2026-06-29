const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? ""

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

export async function apiClient<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  if (!API_BASE) throw new Error("API not configured – set NEXT_PUBLIC_API_URL")
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = (await res.json()) as { detail?: string | { msg?: string }[] }
      if (typeof body.detail === "string") detail = body.detail
      else if (Array.isArray(body.detail) && body.detail[0]?.msg)
        detail = body.detail[0].msg
    } catch {
      /* ignore parse errors */
    }
    throw new Error(detail || `API error: ${res.status}`)
  }

  assertJson(res)
  return res.json() as Promise<T>
}
