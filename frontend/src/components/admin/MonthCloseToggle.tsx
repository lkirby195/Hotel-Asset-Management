"use client";

import { EmptyState } from "@/components/shared/EmptyState";

export function MonthCloseToggle() {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <EmptyState message="Month close controls will be available when the month-close API endpoint is implemented." />
    </div>
  );
}
