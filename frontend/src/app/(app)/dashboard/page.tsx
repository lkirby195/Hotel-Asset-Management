"use client";

import { useState } from "react";
import { ContentHeader } from "@/components/shared/ContentHeader";
import { GoalGrid } from "@/components/dashboard/GoalGrid";
import { GoalDataTable } from "@/components/dashboard/GoalDataTable";
import { GoalSelector } from "@/components/dashboard/GoalSelector";
import { YesterdayKPIs } from "@/components/dashboard/YesterdayKPIs";
import { MTDPaceTable } from "@/components/dashboard/MTDPaceTable";
import { useGoals } from "@/hooks/useGoals";
import { useProperty } from "@/providers/property-provider";
import { GaugeSkeleton } from "@/components/shared/LoadingSkeleton";
import type { GoalInput } from "@/types/goals";

export default function DashboardPage() {
  const { selectedPropertyId } = useProperty();
  const { data: goalsData, isLoading } = useGoals();
  const [selectorOpen, setSelectorOpen] = useState(false);

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
