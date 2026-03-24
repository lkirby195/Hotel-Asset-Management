"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { createApiClient } from "@/lib/api-client";
import { ContentHeader } from "@/components/shared/ContentHeader";
import { DualPanelTable } from "@/components/daily-report/DualPanelTable";
import { Skeleton } from "@/components/ui/skeleton";
import { useProperty } from "@/providers/property-provider";
import type { DailyReportResponse } from "@/types/daily-report";
import type { ApiResponse } from "@/types/api";

const TABS = [
  "Room Performance",
  "Ancillary Revenue",
  "Labor",
  "STR Competitive",
] as const;

type TabName = (typeof TABS)[number];

function toISODate(d: Date): string {
  return (
    d.getFullYear() +
    "-" +
    String(d.getMonth() + 1).padStart(2, "0") +
    "-" +
    String(d.getDate()).padStart(2, "0")
  );
}

function DailyReportSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-[400px] w-full" />
    </div>
  );
}

export default function DailyReportPage() {
  const { selectedPropertyId } = useProperty();
  const { getToken } = useAuth();
  const apiClient = createApiClient(getToken);

  const [activeTab, setActiveTab] = useState<TabName>("Room Performance");
  const [reportDate, setReportDate] = useState<Date>(() => {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    return d;
  });

  const dateStr = toISODate(reportDate);

  const { data, isLoading, error } = useQuery<DailyReportResponse>({
    queryKey: ["daily-report", selectedPropertyId, dateStr],
    queryFn: async () => {
      const resp = await apiClient.get<ApiResponse<DailyReportResponse>>(
        `/daily-report/${selectedPropertyId}?date=${dateStr}`
      );
      return resp.data.data;
    },
    enabled: !!selectedPropertyId,
  });

  const prevDay = () => {
    setReportDate((d) => {
      const next = new Date(d);
      next.setDate(next.getDate() - 1);
      return next;
    });
  };

  const nextDay = () => {
    setReportDate((d) => {
      const next = new Date(d);
      next.setDate(next.getDate() + 1);
      return next;
    });
  };

  if (!selectedPropertyId) {
    return (
      <div className="space-y-6">
        <ContentHeader title="Daily Report" />
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-sm text-gray-500">
          Select a property to view the daily report.
        </div>
      </div>
    );
  }

  const formattedDate = reportDate.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="space-y-6">
      <ContentHeader title="Daily Report" subtitle={data?.property_name} />

      {/* Date navigator */}
      <div className="flex items-center gap-3">
        <button
          onClick={prevDay}
          className="rounded-md border border-gray-300 p-1.5 hover:bg-gray-50"
          aria-label="Previous day"
        >
          <ChevronLeft className="h-4 w-4 text-gray-600" />
        </button>
        <span className="text-sm font-medium text-gray-900">{formattedDate}</span>
        <button
          onClick={nextDay}
          className="rounded-md border border-gray-300 p-1.5 hover:bg-gray-50"
          aria-label="Next day"
        >
          <ChevronRight className="h-4 w-4 text-gray-600" />
        </button>
      </div>

      {/* Tab navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6" aria-label="Report tabs">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={
                tab === activeTab
                  ? "border-b-2 border-brand pb-2 text-sm font-medium text-brand"
                  : "pb-2 text-sm font-medium text-gray-500 hover:text-gray-700"
              }
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {isLoading ? (
        <DailyReportSkeleton />
      ) : error ? (
        <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-sm text-gray-500">
          Failed to load daily report data.
        </div>
      ) : data ? (
        <DualPanelTable sections={data.sections[activeTab] ?? []} />
      ) : null}
    </div>
  );
}
