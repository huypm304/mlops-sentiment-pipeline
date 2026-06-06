import { redirect } from "next/navigation"

/** Legacy route — ops monitoring moved to admin console */
export default function MonitoringRedirectPage() {
  redirect("/admin/monitoring")
}
