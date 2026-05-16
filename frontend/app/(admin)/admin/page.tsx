import { redirect } from "next/navigation"

import { defaultAdminRoute } from "@/lib/constants/admin-navigation"

export default function AdminIndexPage() {
  redirect(defaultAdminRoute)
}
