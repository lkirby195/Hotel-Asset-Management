"use client";

import { ContentHeader } from "@/components/shared/ContentHeader";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import { YesterdayKPIs } from "@/components/dashboard/YesterdayKPIs";
import { MTDPaceTable } from "@/components/dashboard/MTDPaceTable";
import { ForwardLookCards } from "@/components/dashboard/ForwardLookCards";
import { OTBDailyTable } from "@/components/dashboard/OTBDailyTable";
import { DeptSnapshotGrid } from "@/components/dashboard/DeptSnapshotGrid";
import { useProperty } from "@/providers/property-provider";
import type { ForwardLookResponse } from "@/types/dashboard";
import type { ApiResponse } from "@/types/api";

export default function DashboardPage() {
  const { selectedPropertyId } = useProperty();
  const { getToken } = useAuth();

  const apiClient = createApiClient(getToken);
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
      <div className="space-y-6">
        <ContentHeader title="Overview" />
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-sm text-gray-500">
          Select a property to view dashboard.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ContentHeader title="Overview" />

      <section>
        <h2 className="text-sm font-medium text-gray-700 mb-3">Prior Day Summary</h2>
        <YesterdayKPIs propertyId={selectedPropertyId} />
      </section>

      <section>
        <h2 className="text-sm font-medium text-gray-700 mb-3">Month-to-Date Pace</h2>
        <MTDPaceTable propertyId={selectedPropertyId} />
      </section>

      <section>
        <div className="mb-3">
          <h2 className="text-sm font-medium text-gray-700">Forward Look &mdash; On the Books</h2>
          {forwardLookData?.as_of_date && (
            <p className="text-xs text-gray-500 mt-0.5">
              As of {new Date(forwardLookData.as_of_date + "T00:00:00").toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
            </p>
          )}
        </div>
        <div className="space-y-4">
          <ForwardLookCards
            propertyId={selectedPropertyId}
            data={forwardLookData}
            isLoading={forwardLookLoading}
            error={forwardLookError as Error | null}
          />
          <OTBDailyTable data={forwardLookData} isLoading={forwardLookLoading} />
        </div>
      </section>

      <section>
        <h2 className="text-sm font-medium text-gray-700 mb-3">Department Snapshot &mdash; MTD</h2>
        <DeptSnapshotGrid propertyId={selectedPropertyId} />
      </section>
    </div>
  );
}
