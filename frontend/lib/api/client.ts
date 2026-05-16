const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? ""

export async function apiClient<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
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

  return res.json() as Promise<T>
}
