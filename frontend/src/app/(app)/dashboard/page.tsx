"use client";

import { useState } from "react";
import { ContentHeader } from "@/components/shared/ContentHeader";
import { GoalGrid } from "@/components/dashboard/GoalGrid";
import { GoalDataTable } from "@/components/dashboard/GoalDataTable";
import { GoalSelector } from "@/components/dashboard/GoalSelector";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import { YesterdayKPIs } from "@/components/dashboard/YesterdayKPIs";
import { MTDPaceTable } from "@/components/dashboard/MTDPaceTable";
import { ForwardLookCards } from "@/components/dashboard/ForwardLookCards";
import { OTBDailyTable } from "@/components/dashboard/OTBDailyTable";
import { useGoals } from "@/hooks/useGoals";
import { useProperty } from "@/providers/property-provider";
import { GaugeSkeleton } from "@/components/shared/LoadingSkeleton";
import type { GoalInput } from "@/types/goals";
import type { ForwardLookResponse } from "@/types/dashboard";
import type { ApiResponse } from "@/types/api";

export default function DashboardPage() {
  const { selectedPropertyId } = useProperty();
  const { getToken } = useAuth();
  const { data: goalsData, isLoading } = useGoals();
  const [selectorOpen, setSelectorOpen] = useState(false);

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

  const handleSaveGoals = (goals: GoalInput[]) => {
    // TODO: Call useSetGoals mutation when API is ready
    console.log("Saving goals:", goals);
  };

  if (!selectedPropertyId) {
    return (
      <div className="space-y-6">
        <ContentHeader title="Dashboard" />
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-sm text-gray-500">
          Select a property to view dashboard.
        </div>
      </div>
    );
  }

  const goals = goalsData?.goals ?? [];

  return (
    <div className="space-y-6">
      <ContentHeader title="Dashboard" />

      <section>
        <h2 className="text-sm font-medium text-gray-700 mb-3">Yesterday&apos;s Performance</h2>
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
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-gray-700">Annual Goals</h2>
          <button
            onClick={() => setSelectorOpen(true)}
            className="rounded-md bg-brand px-3 py-1.5 text-xs font-medium text-white hover:bg-brand/90"
          >
            Edit Goals
          </button>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <GaugeSkeleton key={i} />
            ))}
          </div>
        ) : goals.length > 0 ? (
          <>
            <GoalGrid goals={goals} />
            <GoalDataTable goals={goals} />
          </>
        ) : (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-sm text-gray-500">
            No goals set yet. Click &quot;Edit Goals&quot; to get started.
          </div>
        )}
      </section>

      <GoalSelector
        isOpen={selectorOpen}
        onClose={() => setSelectorOpen(false)}
        onSave={handleSaveGoals}
      />
    </div>
  );
}
