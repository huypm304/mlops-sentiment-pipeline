import { redirect } from "next/navigation"

import { defaultCustomerRoute } from "@/lib/constants/customer-navigation"

/** Legacy route — customer analysis moved to /reviews */
export default function PredictionRedirectPage() {
  redirect(defaultCustomerRoute)
}
