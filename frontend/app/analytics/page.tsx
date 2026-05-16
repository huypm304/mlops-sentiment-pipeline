import { redirect } from "next/navigation"

/** Legacy route — business analytics moved to /insights */
export default function AnalyticsRedirectPage() {
  redirect("/insights")
}
