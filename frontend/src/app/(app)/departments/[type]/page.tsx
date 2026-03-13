"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { ContentHeader } from "@/components/shared/ContentHeader";
import { PeriodSelector } from "@/components/shared/PeriodSelector";
import { ReportEngine } from "@/components/reports/ReportEngine";
import { useReportData } from "@/hooks/useReportData";
import { useProperty } from "@/providers/property-provider";
import { EmptyState } from "@/components/shared/EmptyState";
import type { PeriodType } from "@/types/reports";

const DEPT_TITLES: Record<string, string> = {
  rooms: "Rooms",
  fb: "Food & Beverage",
  spa: "Spa",
  golf: "Golf",
  retail: "Retail",
  mountain: "Mountain Operations",
  other: "Other Operated Departments",
};

export default function DepartmentPage() {
  const params = useParams();
  const deptType = params.type as string;
  const [period, setPeriod] = useState<PeriodType>("mtd");
  const [customRange, setCustomRange] = useState<{ start: string; end: string } | null>(null);
  const { selectedPropertyId } = useProperty();

  // TODO: Use a department-scoped report endpoint
  const { data, isLoading } = useReportData(
    selectedPropertyId,
    period,
    customRange?.start,
    customRange?.end
  );

  const title = DEPT_TITLES[deptType] ?? deptType;

  if (!selectedPropertyId) {
    return (
      <div className="space-y-6">
        <ContentHeader title={title} />
        <EmptyState message="Select a property to view the department report." />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ContentHeader
        title={title}
        subtitle={data ? data.property_name : undefined}
      >
        <PeriodSelector
          selected={period}
          onChange={(p) => {
            setPeriod(p);
            if (p !== "custom") setCustomRange(null);
          }}
          onCustomRange={(start, end) => setCustomRange({ start, end })}
        />
        <div />
      </ContentHeader>
      <ReportEngine
        data={data ?? null}
        isLoading={isLoading}
        propertyId={selectedPropertyId}
        period={period}
        customStart={customRange?.start}
        customEnd={customRange?.end}
      />
    </div>
  );
}
