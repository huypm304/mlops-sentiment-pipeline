/** Normalize app paths for static export (trailingSlash: true on S3/CloudFront). */
export function appPath(path: string): string {
  const hashIndex = path.indexOf("#")
  const hash = hashIndex >= 0 ? path.slice(hashIndex) : ""
  const withoutHash = hashIndex >= 0 ? path.slice(0, hashIndex) : path
  const [pathname, query = ""] = withoutHash.split("?")

  if (!pathname.startsWith("/")) return path
  if (pathname === "/") return `${pathname}${query ? `?${query}` : ""}${hash}`

  const normalized = pathname.endsWith("/") ? pathname : `${pathname}/`
  const withQuery = query ? `${normalized}?${query}` : normalized
  return `${withQuery}${hash}`
}

export function modelDetailPath(version: string): string {
  return appPath(`/models/detail?version=${encodeURIComponent(version)}`)
}
