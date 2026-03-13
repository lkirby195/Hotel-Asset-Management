"use client";

import { EmptyState } from "@/components/shared/EmptyState";
import { TableSkeleton } from "@/components/shared/LoadingSkeleton";

interface PaceMatrixProps {
  propertyId: string;
  forwardMonths: number;
}

export function PaceMatrix({ propertyId, forwardMonths }: PaceMatrixProps) {
  // Placeholder until the pace API is implemented
  return (
    <EmptyState
      title="Pace report"
      message={`Pace data for ${forwardMonths} forward months will be available when the pace API endpoint is implemented.`}
    />
  );
}
