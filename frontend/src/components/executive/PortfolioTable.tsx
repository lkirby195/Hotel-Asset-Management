"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { Loader2 } from "lucide-react";
import { createApiClient } from "@/lib/api-client";
import { useProperty } from "@/providers/property-provider";
import { cn } from "@/lib/utils";
import type { ApiResponse } from "@/types/api";
import type { PeriodType } from "@/types/reports";

interface PLKPIData {
  property_id: string;
  property_name: string;
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

function fmtDollars(cents: number): string {
  const dollars = Math.abs(cents) / 100;
  const f = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(dollars);
  return cents < 0 ? `(${f})` : f;
}

function variancePct(actual: number, budget: number): number {
  if (budget === 0) return 0;
  return ((actual - budget) / Math.abs(budget)) * 100;
}

function badgeCls(val: number): string {
  if (val === 0) return "text-surface-500 bg-surface-100";
  return val > 0
    ? "text-positive-700 bg-positive-50"
    : "text-negative-700 bg-negative-50";
}

interface PortfolioTableProps {
  period: PeriodType;
}

export function PortfolioTable({ period }: PortfolioTableProps) {
  const { properties } = useProperty();
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const { start, end } = periodDates(period);

  const { data: rows, isLoading } = useQuery<PLKPIData[]>({
    queryKey: ["portfolio-table", period, start, end],
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-5 h-5 animate-spin text-brand-500" />
        <span className="ml-2 text-sm text-surface-500">Loading portfolio data...</span>
      </div>
    );
  }

  if (!rows || rows.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-surface-200 p-12 text-center text-sm text-surface-400">
        No portfolio data available for the selected period.
      </div>
    );
  }

  const isUnderperformer = (row: PLKPIData) => {
    const revVar = variancePct(row.total_revenue, row.total_revenue_budget);
    const ebitdaVar = variancePct(row.ebitda, row.ebitda_budget);
    return revVar < -10 || ebitdaVar < -10;
  };

  return (
    <div className="bg-white rounded-xl border border-surface-200 overflow-x-auto">
      <table className="w-full text-xs whitespace-nowrap">
        <thead className="sticky top-0 z-40">
          <tr className="bg-surface-900 text-white">
            <th className="text-left py-3 px-3 font-semibold min-w-[180px] sticky left-0 bg-surface-900 z-10">
              Property
            </th>
            <th className="text-right py-3 px-3 font-semibold">Occ %</th>
            <th className="text-right py-3 px-3 font-semibold">ADR</th>
            <th className="text-right py-3 px-3 font-semibold">RevPAR</th>
            <th className="text-right py-3 px-3 font-semibold">Revenue</th>
            <th className="text-right py-3 px-3 font-semibold">EBITDA</th>
            <th className="text-right py-3 px-3 font-semibold border-r-2 border-surface-700">
              Margin
            </th>
            <th className="text-right py-3 px-3 font-semibold border-l-2 border-brand-500">
              Rev vs Bgt
            </th>
            <th className="text-right py-3 px-3 font-semibold">EBITDA vs Bgt</th>
            <th className="text-right py-3 px-3 font-semibold">Occ vs Bgt</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-surface-100">
          {rows.map((row) => {
            const revVar = variancePct(row.total_revenue, row.total_revenue_budget);
            const ebitdaVar = variancePct(row.ebitda, row.ebitda_budget);
            const occVar = (row.occupancy - row.occupancy_budget) * 100;
            const margin = row.total_revenue
              ? (row.ebitda / row.total_revenue) * 100
              : 0;
            const alert = isUnderperformer(row);

            return (
              <tr
                key={row.property_id}
                className={cn(
                  "hover:bg-surface-50",
                  alert && "bg-negative-50 hover:bg-negative-100",
                )}
              >
                <td
                  className={cn(
                    "py-2.5 px-3 font-medium sticky left-0 z-10",
                    alert ? "bg-negative-50" : "bg-white",
                  )}
                >
                  {row.property_name}
                  {alert && (
                    <span className="ml-1.5 inline-flex px-1 py-0.5 rounded text-[9px] font-bold text-negative-700 bg-negative-100">
                      ALERT
                    </span>
                  )}
                </td>
                <td className="py-2.5 px-3 text-right">
                  {(row.occupancy * 100).toFixed(1)}%
                </td>
                <td className="py-2.5 px-3 text-right">
                  {fmtDollars(row.adr)}
                </td>
                <td className="py-2.5 px-3 text-right">
                  {fmtDollars(row.revpar)}
                </td>
                <td className="py-2.5 px-3 text-right">
                  {fmtShort(row.total_revenue)}
                </td>
                <td className={cn("py-2.5 px-3 text-right", ebitdaVar < -10 && "text-negative-700")}>
                  {fmtShort(row.ebitda)}
                </td>
                <td className="py-2.5 px-3 text-right border-r-2 border-surface-200">
                  {margin.toFixed(1)}%
                </td>
                <td className="py-2.5 px-3 text-right border-l-2 border-brand-500">
                  <span
                    className={cn(
                      "inline-flex px-1 py-0.5 rounded text-[10px] font-medium",
                      badgeCls(revVar),
                    )}
                  >
                    {revVar >= 0 ? "+" : ""}{revVar.toFixed(1)}%
                  </span>
                </td>
                <td className="py-2.5 px-3 text-right">
                  <span
                    className={cn(
                      "inline-flex px-1 py-0.5 rounded text-[10px] font-medium",
                      badgeCls(ebitdaVar),
                    )}
                  >
                    {ebitdaVar >= 0 ? "+" : ""}{ebitdaVar.toFixed(1)}%
                  </span>
                </td>
                <td className="py-2.5 px-3 text-right">
                  <span
                    className={cn(
                      "inline-flex px-1 py-0.5 rounded text-[10px] font-medium",
                      badgeCls(occVar),
                    )}
                  >
                    {occVar >= 0 ? "+" : ""}{occVar.toFixed(1)}pt
                  </span>
                </td>
              </tr>
            );
          })}

          {/* Portfolio Total Row */}
          {rows.length > 1 && (() => {
            const totRev = rows.reduce((s, r) => s + r.total_revenue, 0);
            const totRevBgt = rows.reduce((s, r) => s + r.total_revenue_budget, 0);
            const totEbitda = rows.reduce((s, r) => s + r.ebitda, 0);
            const totEbitdaBgt = rows.reduce((s, r) => s + r.ebitda_budget, 0);
            const avgOcc = rows.reduce((s, r) => s + r.occupancy, 0) / rows.length;
            const avgOccBgt = rows.reduce((s, r) => s + r.occupancy_budget, 0) / rows.length;
            const avgAdr = rows.reduce((s, r) => s + r.adr, 0) / rows.length;
            const avgRevpar = rows.reduce((s, r) => s + r.revpar, 0) / rows.length;
            const margin = totRev ? (totEbitda / totRev) * 100 : 0;
            const revVarT = variancePct(totRev, totRevBgt);
            const ebitdaVarT = variancePct(totEbitda, totEbitdaBgt);
            const occVarT = (avgOcc - avgOccBgt) * 100;

            return (
              <tr className="bg-surface-900 text-white font-bold">
                <td className="py-3 px-3 sticky left-0 bg-surface-900 z-10">
                  Portfolio Total
                </td>
                <td className="py-3 px-3 text-right">{(avgOcc * 100).toFixed(1)}%</td>
                <td className="py-3 px-3 text-right">{fmtDollars(avgAdr)}</td>
                <td className="py-3 px-3 text-right">{fmtDollars(avgRevpar)}</td>
                <td className="py-3 px-3 text-right">{fmtShort(totRev)}</td>
                <td className="py-3 px-3 text-right">{fmtShort(totEbitda)}</td>
                <td className="py-3 px-3 text-right border-r-2 border-surface-700">{margin.toFixed(1)}%</td>
                <td className="py-3 px-3 text-right border-l-2 border-brand-500">
                  <span className={cn("inline-flex px-1 py-0.5 rounded text-[10px] font-bold", revVarT >= 0 ? "text-positive-300 bg-white/10" : "text-negative-300 bg-white/10")}>
                    {revVarT >= 0 ? "+" : ""}{revVarT.toFixed(1)}%
                  </span>
                </td>
                <td className="py-3 px-3 text-right">
                  <span className={cn("inline-flex px-1 py-0.5 rounded text-[10px] font-bold", ebitdaVarT >= 0 ? "text-positive-300 bg-white/10" : "text-negative-300 bg-white/10")}>
                    {ebitdaVarT >= 0 ? "+" : ""}{ebitdaVarT.toFixed(1)}%
                  </span>
                </td>
                <td className="py-3 px-3 text-right">
                  <span className={cn("inline-flex px-1 py-0.5 rounded text-[10px] font-bold", occVarT >= 0 ? "text-positive-300 bg-white/10" : "text-negative-300 bg-white/10")}>
                    {occVarT >= 0 ? "+" : ""}{occVarT.toFixed(1)}pt
                  </span>
                </td>
              </tr>
            );
          })()}
        </tbody>
      </table>
    </div>
  );
}
