"use client";

import { useState } from "react";
import { ContentHeader } from "@/components/shared/ContentHeader";
import { PaceMatrix } from "@/components/pace/PaceMatrix";
import { useProperty } from "@/providers/property-provider";
import { EmptyState } from "@/components/shared/EmptyState";

export default function PacePage() {
  const [forwardMonths, setForwardMonths] = useState(6);
  const { selectedPropertyId } = useProperty();

  if (!selectedPropertyId) {
    return (
      <div className="space-y-6">
        <ContentHeader title="Pace report" />
        <EmptyState message="Select a property to view pace data." />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ContentHeader title="Pace report">
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500">Show next</label>
          <select
            value={forwardMonths}
            onChange={(e) => setForwardMonths(Number(e.target.value))}
            className="rounded-md border border-gray-200 px-2 py-1 text-xs"
          >
            {Array.from({ length: 12 }, (_, i) => i + 1).map((n) => (
              <option key={n} value={n}>
                {n} month{n > 1 ? "s" : ""}
              </option>
            ))}
          </select>
        </div>
        <div />
      </ContentHeader>
      <PaceMatrix
        propertyId={selectedPropertyId}
        forwardMonths={forwardMonths}
      />
    </div>
  );
}
