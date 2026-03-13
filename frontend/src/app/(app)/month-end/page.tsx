"use client";

import { useState } from "react";
import { ContentHeader } from "@/components/shared/ContentHeader";
import { ReportEngine } from "@/components/reports/ReportEngine";
import { useReportData } from "@/hooks/useReportData";
import { useProperty } from "@/providers/property-provider";
import { EmptyState } from "@/components/shared/EmptyState";

export default function MonthEndPage() {
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const { selectedPropertyId } = useProperty();

  // For month-end, we'll pass a special "month-end" period once the API supports it
  const { data, isLoading } = useReportData(
    selectedPropertyId,
    "mtd",
    undefined,
    undefined
  );

  if (!selectedPropertyId) {
    return (
      <div className="space-y-6">
        <ContentHeader title="Month-end P&L" />
        <EmptyState message="Select a property to view month-end reports." />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ContentHeader
        title="Month-end P&L"
        subtitle={data ? data.property_name : undefined}
      >
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500">Month:</label>
          <select
            value={selectedMonth ?? ""}
            onChange={(e) => setSelectedMonth(e.target.value || null)}
            className="rounded-md border border-gray-200 px-2 py-1 text-xs"
          >
            <option value="">Select a closed month...</option>
          </select>
        </div>
        <div />
      </ContentHeader>
      {selectedMonth ? (
        <ReportEngine
          data={data ?? null}
          isLoading={isLoading}
          propertyId={selectedPropertyId}
          period="mtd"
          showForecast
        />
      ) : (
        <EmptyState message="Select a closed month to view the P&L report." />
      )}
    </div>
  );
}
