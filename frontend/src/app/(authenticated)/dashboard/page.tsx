"use client";

import { useProperty } from "@/providers/property-provider";

export default function DashboardPage() {
  const { selectedPropertyId, properties } = useProperty();
  const selectedProperty = properties.find(
    (p) => p.id === selectedPropertyId
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        {selectedProperty && (
          <p className="text-sm text-gray-500">{selectedProperty.name}</p>
        )}
      </div>
      <div className="rounded-lg border bg-white p-8 text-center text-gray-500">
        Goal tracking dashboard coming in Phase 3.
        <br />
        Navigate to <strong>Inter-Month Report</strong> to view performance
        data.
      </div>
    </div>
  );
}
