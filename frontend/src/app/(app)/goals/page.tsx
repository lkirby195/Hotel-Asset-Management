"use client";

import { useState, useMemo } from "react";
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { X, Plus, Trash2, ChevronDown, ChevronRight } from "lucide-react";
import { ContentHeader } from "@/components/shared/ContentHeader";
import { useProperty } from "@/providers/property-provider";
import { createApiClient } from "@/lib/api-client";
import {
  useGoals,
  useCreateGoal,
  useUpdateGoal,
  useDeleteGoal,
  type GoalFromAPI,
  type GoalCreateInput,
} from "@/hooks/useGoals";
import { cn } from "@/lib/utils";
import type { ApiResponse } from "@/types/api";

/* ── Metric definitions ─────────────────────────── */

const METRIC_DEFS: Record<
  string,
  { label: string; format: "currency" | "percentage"; direction: "gte" | "lte" }
> = {
  revpar: { label: "RevPAR", format: "currency", direction: "gte" },
  occupancy: { label: "Occupancy", format: "percentage", direction: "gte" },
  adr: { label: "ADR", format: "currency", direction: "gte" },
  total_revenue: { label: "Total Revenue", format: "currency", direction: "gte" },
  gop: { label: "GOP", format: "currency", direction: "gte" },
  ebitda: { label: "EBITDA", format: "currency", direction: "gte" },
  labor_pct: { label: "Labor %", format: "percentage", direction: "lte" },
  food_cost_pct: { label: "Food Cost %", format: "percentage", direction: "lte" },
};

const AVAILABLE_METRICS = Object.entries(METRIC_DEFS).map(([code, def]) => ({
  code,
  ...def,
}));

/* ── Formatters ─────────────────────────────────── */

function fmtTarget(value: number, format: "currency" | "percentage"): string {
  if (format === "percentage") return `${(value / 100).toFixed(1)}%`;
  const dollars = value / 100;
  if (dollars >= 1_000_000) return `$${(dollars / 1_000_000).toFixed(1)}M`;
  if (dollars >= 1_000) return `$${Math.round(dollars).toLocaleString()}`;
  return `$${dollars.toFixed(0)}`;
}

/* ── KPI data for progress (actual vs target) ───── */

interface PLKPIData {
  occupancy: number;
  adr: number;
  revpar: number;
  total_revenue: number;
  gop: number;
  ebitda: number;
}

function getActualForMetric(kpi: PLKPIData | undefined, metric: string): number | null {
  if (!kpi) return null;
  switch (metric) {
    case "revpar": return kpi.revpar;
    case "adr": return kpi.adr;
    case "occupancy": return Math.round(kpi.occupancy * 10000); // to basis points
    case "total_revenue": return kpi.total_revenue;
    case "gop": return kpi.gop;
    case "ebitda": return kpi.ebitda;
    default: return null;
  }
}

/* ── Gauge component ────────────────────────────── */

function GoalGauge({
  label,
  actual,
  target,
  format,
}: {
  label: string;
  actual: number | null;
  target: number;
  format: "currency" | "percentage";
}) {
  const pct = actual != null && target > 0 ? Math.min((actual / target) * 100, 150) : 0;
  const displayPct = actual != null && target > 0 ? ((actual / target) * 100).toFixed(1) : "—";
  const favorable = actual != null && actual >= target;

  // SVG arc gauge
  const radius = 60;
  const stroke = 10;
  const circumference = Math.PI * radius; // half circle
  const offset = circumference - (Math.min(pct, 100) / 100) * circumference;

  return (
    <div className="bg-white rounded-lg border border-surface-200 p-4 text-center hover:shadow-md transition-shadow">
      <div className="text-[10px] font-medium text-surface-400 uppercase tracking-wide mb-2">
        {label}
      </div>
      <svg width="140" height="80" viewBox="0 0 140 80" className="mx-auto">
        {/* Background arc */}
        <path
          d="M 10 75 A 60 60 0 0 1 130 75"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={stroke}
          strokeLinecap="round"
        />
        {/* Progress arc */}
        <path
          d="M 10 75 A 60 60 0 0 1 130 75"
          fill="none"
          stroke={favorable ? "#10b981" : actual != null ? "#ef4444" : "#d1d5db"}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700"
        />
        <text x="70" y="60" textAnchor="middle" className="text-lg font-bold fill-current">
          {displayPct}%
        </text>
      </svg>
      <div className="text-xs text-surface-500 mt-1">
        {actual != null ? fmtTarget(actual, format) : "—"}{" "}
        <span className="text-surface-400">/ {fmtTarget(target, format)}</span>
      </div>
    </div>
  );
}

/* ── Monthly breakdown table ────────────────────── */

const MONTH_NAMES = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

interface MonthlyKPI {
  month: number;
  actual: number | null;
  target: number;
}

function MonthlyDrilldown({
  monthlyData,
  format,
}: {
  monthlyData: MonthlyKPI[];
  format: "currency" | "percentage";
}) {
  const currentMonth = new Date().getMonth() + 1;

  return (
    <div className="overflow-hidden rounded-lg border border-surface-200 bg-white mt-2 mb-4">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-surface-50 border-b border-surface-200">
            <th className="text-left py-2 px-3 font-medium text-surface-500">Month</th>
            <th className="text-right py-2 px-3 font-medium text-surface-500">Target</th>
            <th className="text-right py-2 px-3 font-medium text-surface-500">Actual</th>
            <th className="text-right py-2 px-3 font-medium text-surface-500">% of Target</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-surface-100">
          {monthlyData.map((md) => {
            const pctOfGoal = md.actual != null && md.target > 0
              ? ((md.actual / md.target) * 100).toFixed(1)
              : null;
            const isCurrentMonth = md.month === currentMonth;
            const isFuture = md.month > currentMonth;

            return (
              <tr
                key={md.month}
                className={cn(
                  isCurrentMonth && "border-l-2 border-l-brand-500 bg-brand-50/30",
                  isFuture && "text-surface-400",
                )}
              >
                <td className="py-1.5 px-3">{MONTH_NAMES[md.month - 1]}</td>
                <td className="py-1.5 px-3 text-right tabular-nums">
                  {fmtTarget(md.target, format)}
                </td>
                <td className="py-1.5 px-3 text-right tabular-nums">
                  {md.actual != null ? fmtTarget(md.actual, format) : "—"}
                </td>
                <td className={cn(
                  "py-1.5 px-3 text-right tabular-nums",
                  pctOfGoal != null && Number(pctOfGoal) >= 100 && "text-positive-700",
                  pctOfGoal != null && Number(pctOfGoal) < 100 && "text-negative-700",
                )}>
                  {pctOfGoal != null ? `${pctOfGoal}%` : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/* ── Goal editing modal ─────────────────────────── */

function GoalEditModal({
  isOpen,
  onClose,
  existingGoals,
  onSave,
  isSaving,
}: {
  isOpen: boolean;
  onClose: () => void;
  existingGoals: GoalFromAPI[];
  onSave: (goals: GoalCreateInput[]) => void;
  isSaving: boolean;
}) {
  const [drafts, setDrafts] = useState<
    { metric_code: string; target_value: number | string }[]
  >(() =>
    existingGoals.map((g) => ({
      metric_code: g.metric_code,
      target_value: g.target_value,
    })),
  );

  const usedCodes = new Set(drafts.map((d) => d.metric_code));
  const availableMetrics = AVAILABLE_METRICS.filter((m) => !usedCodes.has(m.code));

  const addMetric = (code: string) => {
    setDrafts((prev) => [...prev, { metric_code: code, target_value: "" }]);
  };

  const removeMetric = (idx: number) => {
    setDrafts((prev) => prev.filter((_, i) => i !== idx));
  };

  const updateTarget = (idx: number, value: string) => {
    setDrafts((prev) =>
      prev.map((d, i) => (i === idx ? { ...d, target_value: value } : d)),
    );
  };

  const handleSave = () => {
    const goals: GoalCreateInput[] = drafts
      .filter((d) => d.metric_code && Number(d.target_value) > 0)
      .map((d) => ({
        metric_code: d.metric_code,
        target_value: Number(d.target_value),
        period_type: "annual",
        year: 2026,
      }));
    onSave(goals);
  };

  const canSave = drafts.length > 0 && drafts.every((d) => Number(d.target_value) > 0);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-200">
          <h2 className="text-lg font-medium text-surface-900">Edit Annual Goals</h2>
          <button onClick={onClose} className="text-surface-400 hover:text-surface-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {drafts.map((draft, idx) => {
            const def = METRIC_DEFS[draft.metric_code];
            return (
              <div key={draft.metric_code} className="flex items-center gap-3 border border-surface-200 rounded-lg p-3">
                <button
                  onClick={() => removeMetric(idx)}
                  className="text-surface-400 hover:text-negative-500 shrink-0"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
                <span className="text-sm font-medium text-surface-900 flex-1">
                  {def?.label ?? draft.metric_code}
                </span>
                <div className="flex items-center gap-1.5">
                  <label className="text-xs text-surface-500">Target:</label>
                  <input
                    type="number"
                    value={draft.target_value}
                    onChange={(e) => updateTarget(idx, e.target.value)}
                    className="w-28 rounded border border-surface-200 px-2 py-1 text-xs tabular-nums"
                    placeholder={def?.format === "percentage" ? "basis pts" : "cents"}
                  />
                </div>
              </div>
            );
          })}

          {availableMetrics.length > 0 && (
            <div>
              <div className="text-xs font-medium text-surface-500 mb-2 mt-4">Add metric:</div>
              <div className="border border-surface-200 rounded-lg divide-y divide-surface-100 max-h-40 overflow-y-auto">
                {availableMetrics.map((m) => (
                  <button
                    key={m.code}
                    onClick={() => addMetric(m.code)}
                    className="w-full flex items-center gap-3 px-3 py-2 text-sm text-surface-700 hover:bg-surface-50 text-left"
                  >
                    <Plus className="h-3.5 w-3.5 text-surface-400" />
                    {m.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-surface-200">
          <button
            onClick={onClose}
            className="rounded-md px-4 py-1.5 text-sm text-surface-600 border border-surface-200 hover:bg-surface-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!canSave || isSaving}
            className={cn(
              "rounded-md px-4 py-1.5 text-sm text-white",
              canSave && !isSaving ? "bg-brand hover:bg-brand/90" : "bg-surface-300 cursor-not-allowed",
            )}
          >
            {isSaving ? "Saving..." : "Save Goals"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Page Component ─────────────────────────────── */

export default function GoalsPage() {
  const { selectedPropertyId } = useProperty();
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const { data: goals, isLoading } = useGoals(2026);
  const createGoal = useCreateGoal();
  const deleteGoal = useDeleteGoal();

  const [selectorOpen, setSelectorOpen] = useState(false);
  const [expandedMetric, setExpandedMetric] = useState<string | null>(null);

  // Fetch YTD KPIs for progress
  const ytdStart = "2026-01-01";
  const now = new Date();
  const ytdEnd = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;

  const { data: kpiData } = useQuery<PLKPIData>({
    queryKey: ["goals-kpis", selectedPropertyId, ytdEnd],
    queryFn: async () => {
      const r = await api.get<ApiResponse<PLKPIData>>(
        `/reports/pl-kpis/${selectedPropertyId}?start=${ytdStart}&end=${ytdEnd}`,
      );
      return r.data.data;
    },
    enabled: !!selectedPropertyId,
  });

  // Fetch monthly KPIs for drilldown (Jan-Mar 2026)
  const { data: monthlyKpis } = useQuery<Record<number, PLKPIData>>({
    queryKey: ["goals-monthly-kpis", selectedPropertyId],
    queryFn: async () => {
      const months: Record<number, PLKPIData> = {};
      const currentMonth = new Date().getMonth() + 1;
      for (let m = 1; m <= Math.min(currentMonth, 12); m++) {
        const dim = new Date(2026, m, 0).getDate();
        const mStart = `2026-${String(m).padStart(2, "0")}-01`;
        const mEnd = `2026-${String(m).padStart(2, "0")}-${String(dim).padStart(2, "0")}`;
        try {
          const r = await api.get<ApiResponse<PLKPIData>>(
            `/reports/pl-kpis/${selectedPropertyId}?start=${mStart}&end=${mEnd}`,
          );
          months[m] = r.data.data;
        } catch {
          // skip month if no data
        }
      }
      return months;
    },
    enabled: !!selectedPropertyId,
    staleTime: 10 * 60 * 1000,
  });

  // Build monthly drilldown data for a given goal
  const getMonthlyData = useMemo(() => {
    return (metricCode: string, annualTarget: number): MonthlyKPI[] => {
      const monthlyTarget = Math.round(annualTarget / 12);
      return Array.from({ length: 12 }, (_, i) => {
        const month = i + 1;
        const kpi = monthlyKpis?.[month];
        const actual = getActualForMetric(kpi, metricCode);
        return { month, actual, target: monthlyTarget };
      });
    };
  }, [monthlyKpis]);

  const handleSaveGoals = async (newGoals: GoalCreateInput[]) => {
    // Delete existing goals first, then create new ones
    if (goals) {
      for (const g of goals) {
        await deleteGoal.mutateAsync(g.id);
      }
    }
    for (const g of newGoals) {
      await createGoal.mutateAsync(g);
    }
    setSelectorOpen(false);
  };

  if (!selectedPropertyId) {
    return (
      <div className="space-y-6">
        <ContentHeader title="Goals" />
        <div className="rounded-lg border border-surface-200 bg-white p-8 text-center text-sm text-surface-500">
          Select a property to view goals.
        </div>
      </div>
    );
  }

  const annualGoals = (goals ?? []).filter((g) => g.period_type === "annual");

  return (
    <div className="space-y-6">
      <ContentHeader title="Goals" />

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-surface-700">Annual Goals — 2026</h2>
          <button
            onClick={() => setSelectorOpen(true)}
            className="rounded-md bg-brand px-3 py-1.5 text-xs font-medium text-white hover:bg-brand/90"
          >
            Edit Goals
          </button>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-36 bg-surface-100 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : annualGoals.length > 0 ? (
          <>
            {/* Gauges */}
            <div className="grid grid-cols-3 gap-4">
              {annualGoals.map((goal) => {
                const def = METRIC_DEFS[goal.metric_code];
                const actual = getActualForMetric(kpiData, goal.metric_code);
                return (
                  <div
                    key={goal.id}
                    className="cursor-pointer"
                    onClick={() =>
                      setExpandedMetric((prev) =>
                        prev === goal.metric_code ? null : goal.metric_code,
                      )
                    }
                  >
                    <GoalGauge
                      label={def?.label ?? goal.metric_code}
                      actual={actual}
                      target={goal.target_value}
                      format={def?.format ?? "currency"}
                    />
                    <div className="flex items-center justify-center mt-1 text-[10px] text-surface-400">
                      {expandedMetric === goal.metric_code ? (
                        <ChevronDown className="h-3 w-3" />
                      ) : (
                        <ChevronRight className="h-3 w-3" />
                      )}
                      <span className="ml-0.5">Monthly breakdown</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Monthly drilldown */}
            {expandedMetric && (() => {
              const goal = annualGoals.find((g) => g.metric_code === expandedMetric);
              if (!goal) return null;
              const def = METRIC_DEFS[goal.metric_code];
              return (
                <MonthlyDrilldown
                  monthlyData={getMonthlyData(goal.metric_code, goal.target_value)}
                  format={def?.format ?? "currency"}
                />
              );
            })()}

            {/* Summary table */}
            <div className="overflow-hidden rounded-lg border border-surface-200 bg-white mt-4">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-surface-100 border-b border-surface-200">
                    <th className="text-left py-2.5 px-3 font-medium text-surface-500 uppercase tracking-wide">Metric</th>
                    <th className="text-right py-2.5 px-3 font-medium text-surface-500 uppercase tracking-wide">Annual Target</th>
                    <th className="text-right py-2.5 px-3 font-medium text-surface-500 uppercase tracking-wide">YTD Actual</th>
                    <th className="text-right py-2.5 px-3 font-medium text-surface-500 uppercase tracking-wide">% of Annual</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-100">
                  {annualGoals.map((goal) => {
                    const def = METRIC_DEFS[goal.metric_code];
                    const fmt = def?.format ?? "currency";
                    const actual = getActualForMetric(kpiData, goal.metric_code);
                    const pct = actual != null && goal.target_value > 0
                      ? ((actual / goal.target_value) * 100).toFixed(1)
                      : null;

                    return (
                      <tr key={goal.id} className="hover:bg-surface-50">
                        <td className="py-2 px-3 text-sm font-medium text-surface-900">
                          {def?.label ?? goal.metric_code}
                        </td>
                        <td className="py-2 px-3 text-sm text-right tabular-nums">
                          {fmtTarget(goal.target_value, fmt)}
                        </td>
                        <td className="py-2 px-3 text-sm text-right tabular-nums">
                          {actual != null ? fmtTarget(actual, fmt) : "—"}
                        </td>
                        <td className={cn(
                          "py-2 px-3 text-sm text-right tabular-nums",
                          pct != null && Number(pct) >= 100 && "text-positive-700",
                          pct != null && Number(pct) < 100 && Number(pct) > 0 && "text-negative-700",
                        )}>
                          {pct != null ? `${pct}%` : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <div className="rounded-lg border border-surface-200 bg-white p-8 text-center text-sm text-surface-500">
            No goals set yet. Click &quot;Edit Goals&quot; to get started.
          </div>
        )}
      </section>

      <GoalEditModal
        isOpen={selectorOpen}
        onClose={() => setSelectorOpen(false)}
        existingGoals={annualGoals}
        onSave={handleSaveGoals}
        isSaving={createGoal.isPending || deleteGoal.isPending}
      />
    </div>
  );
}
