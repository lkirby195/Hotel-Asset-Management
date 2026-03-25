"use client";

import { useState } from "react";
import { Download } from "lucide-react";
import { PeriodSelector } from "@/components/shared/PeriodSelector";
import { PortfolioKpis } from "@/components/executive/PortfolioKpis";
import { PortfolioTable } from "@/components/executive/PortfolioTable";
import { useProperty } from "@/providers/property-provider";
import type { PeriodType } from "@/types/reports";

const COLLECTIONS = [
  "All Properties",
  "Select Service",
  "Boutique Collection",
  "Mountain Resorts",
  "Underperformers",
] as const;

export default function PortfolioPage() {
  const [period, setPeriod] = useState<PeriodType>("mtd");
  const [collection, setCollection] = useState<string>(COLLECTIONS[0]);
  const { properties } = useProperty();

  const periodLabel = period === "mtd" ? "MTD" : period === "qtd" ? "QTD" : period === "ytd" ? "YTD" : period.toUpperCase();

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-surface-900">
            Portfolio Overview
          </h2>
          <p className="text-sm text-surface-500 mt-0.5">
            {collection} ({properties.length}) — {periodLabel}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Collection Selector */}
          <div className="flex items-center gap-2 bg-surface-50 border border-surface-200 rounded-lg px-3 py-1.5">
            <select
              value={collection}
              onChange={(e) => setCollection(e.target.value)}
              className="bg-transparent text-sm font-medium text-surface-700 outline-none cursor-pointer"
            >
              {COLLECTIONS.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <PeriodSelector
            selected={period}
            onChange={setPeriod}
            exclude={["t28", "weekly", "custom"]}
          />

          <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-surface-200 rounded-lg hover:bg-surface-50">
            <Download className="w-3.5 h-3.5" /> Export
          </button>
        </div>
      </div>

      {/* KPI Strip */}
      <PortfolioKpis period={period} />

      {/* Property Table */}
      <PortfolioTable period={period} />

      {/* Footer */}
      <div className="text-center text-xs text-surface-400 pb-4">
        Portfolio Overview — {periodLabel} | Data synced via ProfitSword
      </div>
    </div>
  );
}
