"use client";

import { useState } from "react";
import { ContentHeader } from "@/components/shared/ContentHeader";
import { PaceMatrix } from "@/components/pace/PaceMatrix";
import { useProperty } from "@/providers/property-provider";
import { EmptyState } from "@/components/shared/EmptyState";
import { cn } from "@/lib/utils";

type SalesTab = "position" | "pace";

export default function SalesPerformancePage() {
  const [activeTab, setActiveTab] = useState<SalesTab>("position");
  const [forwardMonths, setForwardMonths] = useState(6);
  const { selectedPropertyId } = useProperty();

  if (!selectedPropertyId) {
    return (
      <div className="space-y-6">
        <ContentHeader title="Sales Performance" />
        <EmptyState message="Select a property to view sales performance." />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ContentHeader title="Sales Performance">
        <div className="flex items-center gap-2">
          {(["position", "pace"] as const).map((tab) => (
            <button
              key={tab}
              className={cn(
                "rounded-full px-3.5 py-1 text-xs font-medium transition-colors",
                activeTab === tab
                  ? "bg-brand text-white"
                  : "bg-white text-gray-500 border border-gray-200 hover:border-gray-300"
              )}
              onClick={() => setActiveTab(tab)}
            >
              {tab === "position" ? "Position" : "Pace"}
            </button>
          ))}
        </div>
        {activeTab === "pace" && (
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500">Forward months:</label>
            <select
              value={forwardMonths}
              onChange={(e) => setForwardMonths(Number(e.target.value))}
              className="rounded-md border border-gray-200 px-2 py-1 text-xs"
            >
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
        )}
      </ContentHeader>

      {activeTab === "position" && (
        <EmptyState
          title="Position report"
          message="Position report will be available when the sales performance API is implemented."
        />
      )}

      {activeTab === "pace" && (
        <PaceMatrix propertyId={selectedPropertyId} forwardMonths={forwardMonths} />
      )}
    </div>
  );
}
