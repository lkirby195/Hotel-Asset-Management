"use client";

import { KpiGrid } from "@/components/shared/KpiGrid";
import type { PeriodType } from "@/types/reports";

interface PortfolioKpisProps {
  period: PeriodType;
}

export function PortfolioKpis({ period }: PortfolioKpisProps) {
  // Placeholder until portfolio API is implemented
  const cards = [
    { label: "Portfolio Revenue", value: "--", change: undefined },
    { label: "Avg RevPAR", value: "--", change: undefined },
    { label: "Avg Occupancy", value: "--", change: undefined },
    { label: "Avg GOP Margin", value: "--", change: undefined },
  ];

  return <KpiGrid cards={cards} />;
}
