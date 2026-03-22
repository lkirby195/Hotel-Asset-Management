"use client";

import { useState } from "react";
import { ContentHeader } from "@/components/shared/ContentHeader";
import { PeriodSelector } from "@/components/shared/PeriodSelector";
import { ReportEngine } from "@/components/reports/ReportEngine";
import { useReportData } from "@/hooks/useReportData";
import { useProperty } from "@/providers/property-provider";
import { EmptyState } from "@/components/shared/EmptyState";
import type { PeriodType } from "@/types/reports";

export default function PerformancePage() {
  const [period, setPeriod] = useState<PeriodType>("mtd");
  const [customRange, setCustomRange] = useState<{ start: string; end: string } | null>(null);
  const { selectedPropertyId } = useProperty();
  const { data, isLoading } = useReportData(
    selectedPropertyId,
    period,
    customRange?.start,
    customRange?.end
  );

  if (!selectedPropertyId) {
    return (
      <div className="space-y-6">
        <ContentHeader title="Performance" />
        <EmptyState message="Select a property to view the report." />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ContentHeader
        title="Performance"
        subtitle={
          data
            ? `${data.property_name} | As of ${data.as_of_date}`
            : undefined
        }
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
