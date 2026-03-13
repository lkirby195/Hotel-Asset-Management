"use client";

import { EmptyState } from "@/components/shared/EmptyState";

interface SalesTableProps {
  propertyId: string;
}

export function SalesTable({ propertyId }: SalesTableProps) {
  return (
    <EmptyState
      title="Sales production"
      message="Sales data will be available when the sales API endpoint is implemented."
    />
  );
}
