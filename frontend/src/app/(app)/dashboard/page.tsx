"use client";

import { ContentHeader } from "@/components/shared/ContentHeader";
import { GoalGrid } from "@/components/dashboard/GoalGrid";
import { GoalDataTable } from "@/components/dashboard/GoalDataTable";
import { useProperty } from "@/providers/property-provider";

export default function DashboardPage() {
  const { selectedPropertyId } = useProperty();

  if (!selectedPropertyId) {
    return (
      <div className="space-y-6">
        <ContentHeader title="Goals" />
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-sm text-gray-500">
          Select a property to view goals.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ContentHeader title="Goals" />
      <GoalGrid />
      <GoalDataTable />
    </div>
  );
}
