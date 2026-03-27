"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { createApiClient } from "@/lib/api-client";
import { useProperty } from "@/providers/property-provider";
import { cn } from "@/lib/utils";
import {
  formatCurrency,
  formatVarianceCurrency,
  formatPercent,
  formatVariancePercent,
  formatInteger,
  formatVarianceInteger,
} from "@/lib/formatters";
import type { ApiResponse } from "@/types/api";

/* ── Types ─────────────────────────────────────── */

interface DeptKPI {
  label: string;
  actual: number;
  budget: number;
  variance: number;
  unit: string; // currency, percentage, integer, decimal
}

interface DeptPLLine {
  id: string;
  code: string;
  name: string;
  parent_id: string | null;
  is_summary: boolean;
  data_type: string;
  sort_order: number;
  depth: number;
  actual: number;
  budget: number;
  variance_dollars: number;
  variance_pct: number | null;
  forecast_lock: number | null;
  prior_year_actual: number | null;
  py_variance_dollars: number | null;
  py_variance_pct: number | null;
}

interface DeptDetailResponse {
  property_id: string;
  property_name: string;
  dept_name: string;
  dept_type: string;
  period: string;
  start_date: string;
  end_date: string;
  kpis: DeptKPI[];
  pl_lines: DeptPLLine[];
}

/* ── KPI Formatters ───────────────────────────────── */

function fmtKpiValue(value: number, unit: string): string {
  switch (unit) {
    case "currency":
      return formatCurrency(value);
    case "percentage":
      return formatPercent(value);
    case "integer":
      return formatInteger(value);
    default:
      return value.toFixed(1);
  }
}

function fmtKpiVariance(value: number, unit: string): string {
  switch (unit) {
    case "currency":
      return formatVarianceCurrency(value);
    case "percentage":
      return formatVariancePercent(value);
    case "integer":
      return formatVarianceInteger(value);
    default:
      return value > 0 ? `+${value.toFixed(1)}` : value.toFixed(1);
  }
}

/* ── P&L Cell Formatters ──────────────────────────── */

const currFmt = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function fmtD(cents: number): string {
  const abs = Math.abs(cents) / 100;
  const s = currFmt.format(abs);
  return cents < 0 ? `(${s})` : s;
}

function fmtVarD(cents: number): string {
  if (cents === 0) return "$0";
  return cents > 0 ? fmtD(cents) : `(${fmtD(Math.abs(cents))})`;
}

function fmtP(d: number | null): string {
  if (d == null) return "--";
  const p = Math.abs(d * 100).toFixed(1);
  if (d > 0) return `+${p}%`;
  if (d < 0) return `-${p}%`;
  return `${p}%`;
}

function varClr(v: number, dt: string): string {
  if (v === 0) return "text-surface-500";
  const fav = dt === "expense" ? v < 0 : v > 0;
  return fav ? "text-positive-700" : "text-negative-700";
}

function badgeClr(v: number, dt: string): string {
  if (v === 0) return "text-surface-500 bg-surface-100";
  const fav = dt === "expense" ? v < 0 : v > 0;
  return fav ? "text-positive-700 bg-positive-50" : "text-negative-700 bg-negative-50";
}

/* ── Page Component ────────────────────────────── */

export default function DepartmentPage({
  params,
}: {
  params: { type: string };
}) {
  const deptType = params.type;
  const { selectedPropertyId, properties } = useProperty();
  const { getToken } = useAuth();
  const router = useRouter();
  const api = createApiClient(getToken);
  const property = properties.find((p) => p.id === selectedPropertyId);

  const { data, isLoading, error } = useQuery<DeptDetailResponse>({
    queryKey: ["dept-detail", selectedPropertyId, deptType],
    queryFn: async () => {
      const resp = await api.get<ApiResponse<DeptDetailResponse>>(
        `/reports/dept-detail/${selectedPropertyId}/${deptType}`,
      );
      return resp.data.data;
    },
    enabled: !!selectedPropertyId && selectedPropertyId !== "undefined",
    retry: 1,
  });

  // Debug: log errors
  if (error) {
    console.error("Dept detail fetch error:", error);
  }

  if (!selectedPropertyId) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="rounded-xl border border-surface-200 bg-white p-8 text-center text-sm text-surface-500">
          Select a property to view department data.
        </div>
      </div>
    );
  }

  const kpis = data?.kpis ?? [];
  const plLines = data?.pl_lines ?? [];
  const deptName = data?.dept_name ?? deptType;

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="rounded-xl border border-negative-500/20 bg-negative-50 p-8 text-center text-sm text-negative-700">
          Failed to load department data: {String(error)}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => router.push("/departments")}
          className="flex items-center gap-1 text-sm text-surface-500 hover:text-surface-700 mb-2"
        >
          <ChevronLeft className="w-4 h-4" /> All Departments
        </button>
        <h2 className="text-xl font-bold text-surface-900">{deptName}</h2>
        <p className="text-sm text-surface-500 mt-0.5">
          {property?.name ?? "Property"} -- {data ? `${data.start_date} to ${data.end_date}` : "Month-to-Date"}
        </p>
      </div>

      {/* KPI Cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-lg border border-surface-200 p-4 h-28 animate-pulse"
            />
          ))}
        </div>
      ) : kpis.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {kpis.map((k) => {
            const isFavorable =
              k.unit === "percentage" && (k.label.includes("Cost") || k.label.includes("Labor") || k.label.includes("COGS"))
                ? k.variance <= 0
                : k.variance >= 0;
            return (
              <div
                key={k.label}
                className="bg-white rounded-lg border border-surface-200 p-4"
              >
                <div className="text-[10px] font-medium text-surface-400 uppercase tracking-wide">
                  {k.label}
                </div>
                <div className="text-xl font-bold text-surface-900 mt-1 tabular-nums">
                  {fmtKpiValue(k.actual, k.unit)}
                </div>
                <div className="text-[10px] text-surface-400 mt-0.5">
                  vs {fmtKpiValue(k.budget, k.unit)} budget
                </div>
                <span
                  className={cn(
                    "inline-flex px-1.5 py-0.5 rounded text-xs font-medium mt-1",
                    isFavorable
                      ? "text-positive-700 bg-positive-50"
                      : "text-negative-700 bg-negative-50",
                  )}
                >
                  {fmtKpiVariance(k.variance, k.unit)}
                </span>
              </div>
            );
          })}
        </div>
      ) : null}

      {/* Department P&L Breakdown */}
      {isLoading ? (
        <div className="bg-white rounded-xl border border-surface-200 p-8">
          <div className="space-y-3">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-8 bg-surface-100 rounded animate-pulse" />
            ))}
          </div>
        </div>
      ) : plLines.length === 0 ? (
        <div className="bg-white rounded-xl border border-surface-200 p-8 text-center text-sm text-surface-400">
          No P&L data available for this department.
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-surface-200 overflow-x-auto">
          <table className="w-full text-xs whitespace-nowrap tabular-nums">
            <thead>
              <tr className="bg-surface-900 text-white">
                <th className="text-left py-3 px-4 font-semibold min-w-[200px]">
                  Line Item
                </th>
                <th className="text-right py-3 px-4 font-semibold">Actual</th>
                <th className="text-right py-3 px-4 font-semibold">Budget</th>
                <th className="text-right py-3 px-4 font-semibold">Fcst Lock</th>
                <th className="text-right py-3 px-4 font-semibold border-r-2 border-surface-300/40">
                  STLY
                </th>
                <th className="text-right py-3 px-4 font-semibold border-l-2 border-brand-500">
                  $ Var Bgt
                </th>
                <th className="text-right py-3 px-4 font-semibold">% Var Bgt</th>
                <th className="text-right py-3 px-4 font-semibold">
                  $ Var STLY
                </th>
                <th className="text-right py-3 px-4 font-semibold">
                  % Var STLY
                </th>
              </tr>
            </thead>
            <tbody>
              {plLines.map((line) => {
                const isSummary = line.is_summary;
                const isProfit = line.name.toLowerCase().includes("profit");
                return (
                  <tr
                    key={line.id}
                    className={cn(
                      isSummary && !isProfit && "bg-surface-100 font-semibold",
                      isProfit && "bg-surface-200 font-bold",
                      !isSummary && "hover:bg-surface-50",
                    )}
                  >
                    <td
                      className="py-2 px-4"
                      style={{ paddingLeft: Math.max(0, line.depth - 1) * 20 + 16 }}
                    >
                      {line.name}
                    </td>
                    <td className="py-2 px-4 text-right">{fmtD(line.actual)}</td>
                    <td className={cn("py-2 px-4 text-right", !isSummary && "text-surface-500")}>
                      {fmtD(line.budget)}
                    </td>
                    <td className={cn("py-2 px-4 text-right", !isSummary && "text-surface-500")}>
                      {line.forecast_lock != null ? fmtD(line.forecast_lock) : "--"}
                    </td>
                    <td
                      className={cn(
                        "py-2 px-4 text-right border-r-2 border-surface-300",
                        !isSummary && "text-surface-500",
                      )}
                    >
                      {line.prior_year_actual != null ? fmtD(line.prior_year_actual) : "--"}
                    </td>
                    <td
                      className={cn(
                        "py-2 px-4 text-right border-l-2 border-brand-500",
                        varClr(line.variance_dollars, line.data_type),
                      )}
                    >
                      {fmtVarD(line.variance_dollars)}
                    </td>
                    <td className="py-2 px-4 text-right">
                      <span
                        className={cn(
                          "inline-flex px-1 py-0.5 rounded text-[10px] font-medium",
                          badgeClr(line.variance_dollars, line.data_type),
                        )}
                      >
                        {fmtP(line.variance_pct)}
                      </span>
                    </td>
                    <td
                      className={cn(
                        "py-2 px-4 text-right",
                        varClr(line.py_variance_dollars ?? 0, line.data_type),
                      )}
                    >
                      {line.py_variance_dollars != null
                        ? fmtVarD(line.py_variance_dollars)
                        : "--"}
                    </td>
                    <td className="py-2 px-4 text-right">
                      <span
                        className={cn(
                          "inline-flex px-1 py-0.5 rounded text-[10px] font-medium",
                          badgeClr(line.py_variance_dollars ?? 0, line.data_type),
                        )}
                      >
                        {fmtP(line.py_variance_pct)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
