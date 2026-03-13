"use client";

import { EmptyState } from "@/components/shared/EmptyState";
import type { PeriodType } from "@/types/reports";

interface PortfolioTableProps {
  period: PeriodType;
}

export function PortfolioTable({ period }: PortfolioTableProps) {
  return (
    <EmptyState
      title="Portfolio overview"
      message="Portfolio property comparison table will be available when the executive API endpoint is implemented."
    />
  );
}
