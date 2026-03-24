"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import { Download } from "lucide-react";
import { YesterdayKPIs } from "@/components/dashboard/YesterdayKPIs";
import { MTDPaceTable } from "@/components/dashboard/MTDPaceTable";
import { ForwardLookCards } from "@/components/dashboard/ForwardLookCards";
import { OTBDailyTable } from "@/components/dashboard/OTBDailyTable";
import { DeptSnapshotGrid } from "@/components/dashboard/DeptSnapshotGrid";
import { useProperty } from "@/providers/property-provider";
import { useRole } from "@/hooks/useRole";
import type { ForwardLookResponse } from "@/types/dashboard";
import type { ApiResponse } from "@/types/api";

function SectionHeader({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <h3 className="text-sm font-semibold text-surface-500 uppercase tracking-wider">
        {title}
      </h3>
      {subtitle && <span className="text-xs text-surface-400">{subtitle}</span>}
    </div>
  );
}

export default function DashboardPage() {
  const { selectedPropertyId, properties } = useProperty();
  const { user } = useRole();
  const { getToken } = useAuth();
  const apiClient = createApiClient(getToken);

  const selectedProperty = properties.find((p) => p.id === selectedPropertyId);

  const {
    data: forwardLookData,
    isLoading: forwardLookLoading,
    error: forwardLookError,
  } = useQuery<ForwardLookResponse>({
    queryKey: ["dashboard", "forward-look", selectedPropertyId],
    queryFn: async () => {
      const resp = await apiClient.get<ApiResponse<ForwardLookResponse>>(
        `/dashboard/forward-look/${selectedPropertyId}`
      );
      return resp.data.data;
    },
    enabled: !!selectedPropertyId,
  });

  if (!selectedPropertyId) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="rounded-xl border border-surface-200 bg-white p-8 text-center text-sm text-surface-500">
          Select a property to view dashboard.
        </div>
      </div>
    );
  }

  const today = new Date();
  const greeting =
    today.getHours() < 12
      ? "Good Morning"
      : today.getHours() < 17
        ? "Good Afternoon"
        : "Good Evening";
  const firstName = user?.name?.split(" ")[0] ?? "there";
  const dateString = today.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  const asOfSubtitle = forwardLookData?.as_of_date
    ? `as of ${new Date(forwardLookData.as_of_date + "T00:00:00").toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}`
    : undefined;

  return (
    <div className="max-w-7xl mx-auto px-6 py-6">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-surface-900">
            {greeting}, {firstName}
          </h2>
          <p className="text-sm text-surface-500 mt-0.5">
            {selectedProperty?.name ?? "Property"} &mdash; {dateString}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-surface-200 rounded-lg hover:bg-surface-50 transition-colors">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Section 1: Yesterday's Performance */}
      <div className="mb-8">
        <SectionHeader title="Yesterday's Performance" />
        <YesterdayKPIs propertyId={selectedPropertyId} />
      </div>

      {/* Section 2: Month-to-Date Pace */}
      <div className="mb-8">
        <SectionHeader title="Month-to-Date Pace" />
        <MTDPaceTable propertyId={selectedPropertyId} />
      </div>

      {/* Section 3: Forward Look — On the Books */}
      <div className="mb-8">
        <SectionHeader
          title="Forward Look &mdash; On the Books"
          subtitle={asOfSubtitle}
        />
        <div className="space-y-4">
          <ForwardLookCards
            propertyId={selectedPropertyId}
            data={forwardLookData}
            isLoading={forwardLookLoading}
            error={forwardLookError as Error | null}
          />
          <OTBDailyTable data={forwardLookData} isLoading={forwardLookLoading} />
        </div>
      </div>

      {/* Section 4: Department Snapshot — MTD */}
      <div className="mb-8">
        <SectionHeader title="Department Snapshot &mdash; MTD" />
        <DeptSnapshotGrid propertyId={selectedPropertyId} />
      </div>
    </div>
  );
}
