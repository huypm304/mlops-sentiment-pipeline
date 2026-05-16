import { redirect } from "next/navigation"

import { defaultAdminRoute } from "@/lib/constants/admin-navigation"

/** Legacy route — ops monitoring moved to admin console */
export default function MonitoringRedirectPage() {
  redirect(defaultAdminRoute)
}
