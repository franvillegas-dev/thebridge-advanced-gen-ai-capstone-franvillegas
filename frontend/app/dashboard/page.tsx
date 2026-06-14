import { DashboardGrid } from "@/components/dashboard/DashboardGrid"

export default function DashboardPage() {
  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-6">Dashboard</h1>
      <DashboardGrid />
    </div>
  )
}
