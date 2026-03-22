"use client";

import { useState } from "react";
import { ContentHeader } from "@/components/shared/ContentHeader";
import { GoalGrid } from "@/components/dashboard/GoalGrid";
import { GoalDataTable } from "@/components/dashboard/GoalDataTable";
import { GoalSelector } from "@/components/dashboard/GoalSelector";
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
        <ContentHeader title="Annual Goals" />
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-sm text-gray-500">
          Select a property to view goals.
        </div>
      </div>
    );
  }

  const goals = goalsData?.goals ?? [];

  return (
    <div className="space-y-6">
      <ContentHeader title="Annual Goals">
        <button
          onClick={() => setSelectorOpen(true)}
          className="rounded-md bg-brand px-3 py-1.5 text-xs font-medium text-white hover:bg-brand/90"
        >
          Edit Goals
        </button>
      </ContentHeader>

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
          No goals set yet. Click "Edit Goals" to get started.
        </div>
      )}

      <GoalSelector
        isOpen={selectorOpen}
        onClose={() => setSelectorOpen(false)}
        onSave={handleSaveGoals}
      />
    </div>
  );
}
