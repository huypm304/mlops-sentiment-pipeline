import { redirect } from "next/navigation"

import { defaultCustomerRoute } from "@/lib/constants/customer-navigation"

export default function HomePage() {
  redirect(defaultCustomerRoute)
}
