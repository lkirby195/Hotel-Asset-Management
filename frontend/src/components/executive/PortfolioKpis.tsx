"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import { useProperty } from "@/providers/property-provider";
import { cn } from "@/lib/utils";
import type { ApiResponse } from "@/types/api";
import type { PeriodType } from "@/types/reports";

interface PLKPIData {
  property_id: string;
  occupancy: number;
  occupancy_budget: number;
  adr: number;
  adr_budget: number;
  revpar: number;
  revpar_budget: number;
  total_revenue: number;
  total_revenue_budget: number;
  ebitda: number;
  ebitda_budget: number;
  gop: number;
  gop_budget: number;
  gop_margin: number;
  gop_margin_budget: number;
}

function periodDates(period: PeriodType): { start: string; end: string } {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth();
  switch (period) {
    case "ytd":
      return {
        start: `${y}-01-01`,
        end: `${y}-${String(m + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`,
      };
    case "qtd": {
      const qStart = Math.floor(m / 3) * 3;
      return {
        start: `${y}-${String(qStart + 1).padStart(2, "0")}-01`,
        end: `${y}-${String(m + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`,
      };
    }
    default: {
      return {
        start: `${y}-${String(m + 1).padStart(2, "0")}-01`,
        end: `${y}-${String(m + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`,
      };
    }
  }
}

function fmtShort(cents: number): string {
  const dollars = Math.abs(cents) / 100;
  const neg = cents < 0;
  const wrap = (s: string) => (neg ? `(${s})` : s);
  if (dollars >= 1_000_000) return wrap(`$${(dollars / 1_000_000).toFixed(1)}M`);
  if (dollars >= 1_000) return wrap(`$${Math.round(dollars / 1_000)}K`);
  return wrap(`$${Math.round(dollars)}`);
}

interface PortfolioKpisProps {
  period: PeriodType;
}

export function PortfolioKpis({ period }: PortfolioKpisProps) {
  const { properties } = useProperty();
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const { start, end } = periodDates(period);

  const { data: kpiResults } = useQuery<PLKPIData[]>({
    queryKey: ["portfolio-kpis", period, start, end],
    queryFn: async () => {
      const promises = properties.map((p) =>
        api
          .get<ApiResponse<PLKPIData>>(
            `/reports/pl-kpis/${p.id}?start=${start}&end=${end}`,
          )
          .then((r) => r.data.data)
          .catch(() => null),
      );
      const results = await Promise.all(promises);
      return results.filter((r): r is PLKPIData => r != null);
    },
    enabled: properties.length > 0,
  });

  const agg = kpiResults && kpiResults.length > 0
    ? (() => {
        // Use revenue-weighted averages for rate metrics (occupancy, ADR, RevPAR)
        const totalRev = kpiResults.reduce((s, k) => s + k.total_revenue, 0);
        const totalRevBgt = kpiResults.reduce((s, k) => s + k.total_revenue_budget, 0);
        const totalEbitda = kpiResults.reduce((s, k) => s + k.ebitda, 0);
        const totalEbitdaBgt = kpiResults.reduce((s, k) => s + k.ebitda_budget, 0);

        // TODO: weighted avg should use room nights when available; total_revenue proxy for now
        const revWeight = totalRev || 1;
        const revBgtWeight = totalRevBgt || 1;

        const avgOcc = kpiResults.reduce((s, k) => s + k.occupancy * k.total_revenue, 0) / revWeight;
        const avgOccBgt = kpiResults.reduce((s, k) => s + k.occupancy_budget * k.total_revenue_budget, 0) / revBgtWeight;
        const avgAdr = kpiResults.reduce((s, k) => s + k.adr * k.total_revenue, 0) / revWeight;
        const avgAdrBgt = kpiResults.reduce((s, k) => s + k.adr_budget * k.total_revenue_budget, 0) / revBgtWeight;
        const avgRevpar = kpiResults.reduce((s, k) => s + k.revpar * k.total_revenue, 0) / revWeight;
        const avgRevparBgt = kpiResults.reduce((s, k) => s + k.revpar_budget * k.total_revenue_budget, 0) / revBgtWeight;

        return {
          avgOcc,
          avgOccBgt,
          avgAdr,
          avgAdrBgt,
          avgRevpar,
          avgRevparBgt,
          totalRev,
          totalRevBgt,
          totalEbitda,
          totalEbitdaBgt,
          count: kpiResults.length,
          beating: kpiResults.filter((k) => k.total_revenue >= k.total_revenue_budget).length,
        };
      })()
    : null;

  const cards = agg
    ? [
        {
          label: "Portfolio Occ",
          value: `${(agg.avgOcc * 100).toFixed(1)}%`,
          badge: `${((agg.avgOcc - agg.avgOccBgt) * 100).toFixed(1)}pt vs Bgt`,
          favorable: agg.avgOcc >= agg.avgOccBgt,
        },
        {
          label: "Portfolio ADR",
          value: fmtShort(agg.avgAdr),
          badge: `${agg.avgAdr >= agg.avgAdrBgt ? "+" : ""}${(((agg.avgAdr - agg.avgAdrBgt) / (agg.avgAdrBgt || 1)) * 100).toFixed(1)}%`,
          favorable: agg.avgAdr >= agg.avgAdrBgt,
        },
        {
          label: "Portfolio RevPAR",
          value: fmtShort(agg.avgRevpar),
          badge: `${agg.avgRevpar >= agg.avgRevparBgt ? "+" : ""}${(((agg.avgRevpar - agg.avgRevparBgt) / (agg.avgRevparBgt || 1)) * 100).toFixed(1)}%`,
          favorable: agg.avgRevpar >= agg.avgRevparBgt,
        },
        {
          label: "Total Revenue",
          value: fmtShort(agg.totalRev),
          badge: `${agg.totalRev >= agg.totalRevBgt ? "+" : ""}${fmtShort(agg.totalRev - agg.totalRevBgt)}`,
          favorable: agg.totalRev >= agg.totalRevBgt,
        },
        {
          label: "Total EBITDA",
          value: fmtShort(agg.totalEbitda),
          badge: `${agg.totalEbitda >= agg.totalEbitdaBgt ? "+" : ""}${fmtShort(agg.totalEbitda - agg.totalEbitdaBgt)}`,
          favorable: agg.totalEbitda >= agg.totalEbitdaBgt,
        },
        {
          label: "EBITDA Margin",
          value: agg.totalRev
            ? `${((agg.totalEbitda / agg.totalRev) * 100).toFixed(1)}%`
            : "—",
          badge: "",
          favorable: true,
        },
        {
          label: "Properties Beating Bgt",
          value: `${agg.beating} / ${agg.count}`,
          badge: `${((agg.beating / agg.count) * 100).toFixed(1)}%`,
          favorable: agg.beating > agg.count / 2,
        },
      ]
    : [
        { label: "Portfolio Occ", value: "—", badge: "", favorable: true },
        { label: "Portfolio ADR", value: "—", badge: "", favorable: true },
        { label: "Portfolio RevPAR", value: "—", badge: "", favorable: true },
        { label: "Total Revenue", value: "—", badge: "", favorable: true },
        { label: "Total EBITDA", value: "—", badge: "", favorable: true },
        { label: "EBITDA Margin", value: "—", badge: "", favorable: true },
        { label: "Properties Beating Bgt", value: "—", badge: "", favorable: true },
      ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
      {cards.map((k) => (
        <div
          key={k.label}
          className="bg-white rounded-lg border border-surface-200 p-3 text-center hover:shadow-md transition-shadow"
        >
          <div className="text-[10px] font-medium text-surface-400 uppercase tracking-wide">
            {k.label}
          </div>
          <div className="text-lg font-bold">{k.value}</div>
          {k.badge && (
            <span
              className={cn(
                "inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium",
                k.favorable
                  ? "text-positive-700 bg-positive-50"
                  : "text-negative-700 bg-negative-50",
              )}
            >
              {k.badge}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
