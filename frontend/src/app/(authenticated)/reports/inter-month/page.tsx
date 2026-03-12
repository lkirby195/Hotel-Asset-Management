"use client";

import { useState } from "react";
import { PeriodToolbar } from "@/components/reports/period-toolbar";
import { ReportTable } from "@/components/reports/report-table";
import { useInterMonthReport } from "@/hooks/use-inter-month-report";
import { useProperty } from "@/providers/property-provider";
import type { Period } from "@/lib/types";

export default function InterMonthPage() {
  const [period, setPeriod] = useState<Period>("mtd");
  const [dateRange, setDateRange] = useState<{
    start?: string;
    end?: string;
  }>({});
  const { selectedPropertyId } = useProperty();
  const { data, isLoading } = useInterMonthReport(
    period,
    dateRange.start,
    dateRange.end
  );

  const handlePeriodChange = (
    newPeriod: Period,
    start?: string,
    end?: string
  ) => {
    setPeriod(newPeriod);
    setDateRange({ start, end });
  };

  if (!selectedPropertyId) {
    return (
      <div className="py-12 text-center text-gray-500">
        Select a property to view the report.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Inter-Month Performance</h1>
          {data && (
            <p className="text-sm text-gray-500">
              {data.property_name} | {data.start_date} – {data.end_date}
            </p>
          )}
        </div>
        <PeriodToolbar value={period} onChange={handlePeriodChange} />
      </div>
      <ReportTable
        lines={data?.lines ?? []}
        period={period}
        isLoading={isLoading}
      />
    </div>
  );
}
