import { redirect } from "next/navigation"

/** Legacy route — analytics moved to admin control plane */
export default function AnalyticsRedirectPage() {
  redirect("/admin/analytics")
}
