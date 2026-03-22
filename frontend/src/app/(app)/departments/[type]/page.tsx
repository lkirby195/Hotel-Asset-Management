"use client";

import { ContentHeader } from "@/components/shared/ContentHeader";
import { EmptyState } from "@/components/shared/EmptyState";

const DEPT_TITLES: Record<string, string> = {
  rooms: "Rooms",
  fb: "Food & Beverage",
  spa: "Spa",
  golf: "Golf",
  retail: "Retail",
  mountain: "Mountain Operations",
  other: "Other Operated Departments",
};

export default function DepartmentPage({
  params,
}: {
  params: { type: string };
}) {
  const title = DEPT_TITLES[params.type] ?? params.type;

  return (
    <div className="space-y-6">
      <ContentHeader title={title} />
      <EmptyState
        title="Department reports"
        message="Department-level reporting is coming soon. Use the Performance tab for department data in the meantime."
      />
    </div>
  );
}
