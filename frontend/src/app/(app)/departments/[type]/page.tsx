"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { createApiClient } from "@/lib/api-client";
import { useProperty } from "@/providers/property-provider";
import { cn } from "@/lib/utils";
import type { ApiResponse } from "@/types/api";

/* ── Config ────────────────────────────────────── */

const DEPT_TITLES: Record<string, string> = {
  rooms: "Rooms",
  fb: "Food & Beverage",
  spa: "Spa",
  golf: "Golf",
  retail: "Retail",
  mountain: "Mountain Operations",
  "mountain-ops": "Mountain Operations",
  other: "Other Operated Departments",
};

/* ── Types ─────────────────────────────────────── */

interface DeptLineItem {
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

interface DeptReportData {
  property_id: string;
  property_name: string;
  period: string;
  start_date: string;
  end_date: string;
  lines: DeptLineItem[];
}

/* ── Formatters ────────────────────────────────── */

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
  if (d == null) return "—";
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

/* ── KPI extraction ────────────────────────────── */

interface KPI {
  label: string;
  value: string;
  badge: string;
  favorable: boolean;
}

function extractDeptKPIs(lines: DeptLineItem[], deptType: string): KPI[] {
  const kpis: KPI[] = [];

  // Find revenue and profit lines
  const revLine = lines.find(
    (l) =>
      l.depth <= 1 &&
      l.is_summary &&
      l.data_type === "revenue",
  );
  const profitLine = lines.find(
    (l) => l.name.toLowerCase().includes("profit") || l.name.toLowerCase().includes("dept profit"),
  );

  if (revLine) {
    kpis.push({
      label: "Revenue",
      value: fmtD(revLine.actual),
      badge: fmtVarD(revLine.variance_dollars),
      favorable: revLine.variance_dollars >= 0,
    });
  }

  // Find expense total
  const expLine = lines.find(
    (l) =>
      l.depth <= 1 &&
      l.is_summary &&
      l.data_type === "expense",
  );
  if (expLine) {
    kpis.push({
      label: "Expenses",
      value: fmtD(expLine.actual),
      badge: fmtVarD(expLine.variance_dollars),
      favorable: expLine.variance_dollars <= 0,
    });
  }

  if (profitLine) {
    kpis.push({
      label: "Dept Profit",
      value: fmtD(profitLine.actual),
      badge: fmtVarD(profitLine.variance_dollars),
      favorable: profitLine.variance_dollars >= 0,
    });

    // Profit margin
    if (revLine && revLine.actual !== 0) {
      const margin = (profitLine.actual / revLine.actual) * 100;
      const budgetMargin =
        revLine.budget !== 0
          ? (profitLine.budget / revLine.budget) * 100
          : 0;
      const diff = margin - budgetMargin;
      kpis.push({
        label: "Profit Margin",
        value: `${margin.toFixed(1)}%`,
        badge: `${diff >= 0 ? "+" : ""}${diff.toFixed(1)}pt`,
        favorable: diff >= 0,
      });
    }
  }

  return kpis;
}

/* ── Page Component ────────────────────────────── */

export default function DepartmentPage({
  params,
}: {
  params: { type: string };
}) {
  const deptType = params.type;
  const title = DEPT_TITLES[deptType] ?? deptType;
  const { selectedPropertyId, properties } = useProperty();
  const { getToken } = useAuth();
  const router = useRouter();
  const api = createApiClient(getToken);
  const property = properties.find((p) => p.id === selectedPropertyId);

  // Fetch MTD report
  const { data: report, isLoading } = useQuery<DeptReportData>({
    queryKey: ["dept-report", selectedPropertyId, deptType],
    queryFn: async () => {
      const resp = await api.get<ApiResponse<DeptReportData>>(
        `/reports/inter-month/${selectedPropertyId}?period=mtd`,
      );
      return resp.data.data;
    },
    enabled: !!selectedPropertyId,
  });

  // Filter lines to this department
  const allLines = report?.lines ?? [];

  // Find the department's root line item and its descendants
  const deptLines = filterDeptLines(allLines, deptType);
  const kpis = extractDeptKPIs(deptLines, deptType);

  if (!selectedPropertyId) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="rounded-xl border border-surface-200 bg-white p-8 text-center text-sm text-surface-500">
          Select a property to view department data.
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
        <h2 className="text-xl font-bold text-surface-900">{title}</h2>
        <p className="text-sm text-surface-500 mt-0.5">
          {property?.name ?? "Property"} — Month-to-Date
        </p>
      </div>

      {/* KPI Cards */}
      {kpis.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {kpis.map((k) => (
            <div
              key={k.label}
              className="bg-white rounded-lg border border-surface-200 p-4"
            >
              <div className="text-[10px] font-medium text-surface-400 uppercase tracking-wide">
                {k.label}
              </div>
              <div className="text-xl font-bold text-surface-900 mt-1">
                {k.value}
              </div>
              <span
                className={cn(
                  "inline-flex px-1.5 py-0.5 rounded text-xs font-medium mt-1",
                  k.favorable
                    ? "text-positive-700 bg-positive-50"
                    : "text-negative-700 bg-negative-50",
                )}
              >
                {k.badge}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Department P&L Breakdown */}
      {isLoading ? (
        <div className="bg-white rounded-xl border border-surface-200 p-8">
          <div className="space-y-3">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-8 bg-surface-100 rounded animate-pulse" />
            ))}
          </div>
        </div>
      ) : deptLines.length === 0 ? (
        <div className="bg-white rounded-xl border border-surface-200 p-8 text-center text-sm text-surface-400">
          No data available for this department.
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
              {deptLines.map((line) => {
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
                    <td
                      className={cn(
                        "py-2 px-4 text-right border-r-2 border-surface-300",
                        !isSummary && "text-surface-500",
                      )}
                    >
                      {line.prior_year_actual != null ? fmtD(line.prior_year_actual) : "—"}
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
                        : "—"}
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

/* ── Filter lines to department ────────────────── */

const DEPT_TYPE_KEYWORDS: Record<string, string[]> = {
  rooms: ["room"],
  fb: ["food", "f&b", "beverage", "restaurant"],
  spa: ["spa"],
  golf: ["golf"],
  retail: ["retail"],
  mountain: ["mountain"],
  "mountain-ops": ["mountain"],
  other: ["other operated"],
};

function filterDeptLines(lines: DeptLineItem[], deptType: string): DeptLineItem[] {
  const keywords = DEPT_TYPE_KEYWORDS[deptType] ?? [deptType];

  // Find the root department line item
  const root = lines.find(
    (l) =>
      l.depth === 0 &&
      l.is_summary &&
      keywords.some((kw) => l.name.toLowerCase().includes(kw)),
  );

  if (!root) {
    // Fallback: return lines that match keywords at any depth
    return lines.filter((l) =>
      keywords.some((kw) => l.name.toLowerCase().includes(kw)),
    );
  }

  // Collect root and all descendants
  const rootId = root.id;
  const result: DeptLineItem[] = [];
  const includedIds = new Set<string>([rootId]);

  // Sort by sort_order to process in tree order
  const sorted = [...lines].sort((a, b) => a.sort_order - b.sort_order);

  for (const line of sorted) {
    if (line.id === rootId || (line.parent_id && includedIds.has(line.parent_id))) {
      result.push(line);
      includedIds.add(line.id);
    }
  }

  return result;
}
