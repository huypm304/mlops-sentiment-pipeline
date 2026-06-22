import { redirect } from "next/navigation"

export default function PredictionRedirectPage() {
  redirect("/inference")
}
