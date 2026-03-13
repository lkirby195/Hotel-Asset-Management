"use client";

import { ContentHeader } from "@/components/shared/ContentHeader";
import { SalesTable } from "@/components/sales/SalesTable";
import { useProperty } from "@/providers/property-provider";
import { EmptyState } from "@/components/shared/EmptyState";

export default function SalesPage() {
  const { selectedPropertyId } = useProperty();

  if (!selectedPropertyId) {
    return (
      <div className="space-y-6">
        <ContentHeader title="Sales production" />
        <EmptyState message="Select a property to view sales data." />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ContentHeader title="Sales production" />
      <SalesTable propertyId={selectedPropertyId} />
    </div>
  );
}
