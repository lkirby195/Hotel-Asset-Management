"use client";

import { useState } from "react";
import { ContentHeader } from "@/components/shared/ContentHeader";
import { PeriodSelector } from "@/components/shared/PeriodSelector";
import { PortfolioKpis } from "@/components/executive/PortfolioKpis";
import { PortfolioTable } from "@/components/executive/PortfolioTable";
import type { PeriodType } from "@/types/reports";

export default function PortfolioPage() {
  const [period, setPeriod] = useState<PeriodType>("mtd");

  return (
    <div className="space-y-6">
      <ContentHeader title="Portfolio">
        <PeriodSelector
          selected={period}
          onChange={setPeriod}
          exclude={["t28", "weekly", "custom"]}
        />
        <div />
      </ContentHeader>
      <PortfolioKpis period={period} />
      <PortfolioTable period={period} />
    </div>
  );
}
