"use client";

import { useState, useMemo } from "react";
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { X, Plus, Trash2 } from "lucide-react";
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

/* -- Metric definitions --------------------------------------------------- */

const METRIC_DEFS: Record<
  string,
  { label: string; format: "currency" | "percentage"; inverse: boolean; cumulative: boolean }
> = {
  revpar: { label: "RevPAR", format: "currency", inverse: false, cumulative: false },
  occupancy: { label: "Occupancy", format: "percentage", inverse: false, cumulative: false },
  adr: { label: "ADR", format: "currency", inverse: false, cumulative: false },
  total_revenue: { label: "Total Revenue", format: "currency", inverse: false, cumulative: true },
  gop: { label: "GOP", format: "currency", inverse: false, cumulative: true },
  ebitda: { label: "EBITDA", format: "currency", inverse: false, cumulative: true },
  labor_pct: { label: "Labor %", format: "percentage", inverse: true, cumulative: false },
  food_cost_pct: { label: "Food Cost %", format: "percentage", inverse: true, cumulative: false },
};

const AVAILABLE_METRICS = Object.entries(METRIC_DEFS).map(([code, def]) => ({
  code,
  ...def,
}));

/* -- Formatters ----------------------------------------------------------- */

function fmtValue(value: number, format: "currency" | "percentage"): string {
  if (format === "percentage") return `${(value / 100).toFixed(1)}%`;
  const dollars = value / 100;
  if (Math.abs(dollars) >= 1_000_000)
    return `$${(dollars / 1_000_000).toFixed(2)}M`;
  if (Math.abs(dollars) >= 1_000) return `$${Math.round(dollars).toLocaleString()}`;
  return `$${dollars.toFixed(0)}`;
}

function fmtVariance(
  value: number,
  format: "currency" | "percentage",
): string {
  const sign = value >= 0 ? "+" : "";
  if (format === "percentage") return `${sign}${(value / 100).toFixed(1)}pt`;
  const dollars = value / 100;
  if (Math.abs(dollars) >= 1_000_000)
    return `${sign}$${(dollars / 1_000_000).toFixed(2)}M`;
  if (Math.abs(dollars) >= 1_000)
    return `${sign}$${Math.round(dollars).toLocaleString()}`;
  return `${sign}$${dollars.toFixed(0)}`;
}

/* -- KPI data ------------------------------------------------------------- */

interface PLKPIData {
  occupancy: number;
  adr: number;
  revpar: number;
  total_revenue: number;
  gop: number;
  ebitda: number;
  // TODO: add labor_pct and food_cost_pct to the pl-kpis endpoint response
  total_labor?: number;
  fb_cost_of_sales?: number;
  fb_revenue?: number;
}

function getActualForMetric(
  kpi: PLKPIData | undefined,
  metric: string,
): number | null {
  if (!kpi) return null;
  switch (metric) {
    case "revpar":
      return kpi.revpar;
    case "adr":
      return kpi.adr;
    case "occupancy":
      return Math.round(kpi.occupancy * 10000);
    case "total_revenue":
      return kpi.total_revenue;
    case "gop":
      return kpi.gop;
    case "ebitda":
      return kpi.ebitda;
    case "labor_pct":
      // Compute from total_labor / total_revenue if available
      if (kpi.total_labor != null && kpi.total_revenue > 0) {
        return Math.round((kpi.total_labor / kpi.total_revenue) * 10000);
      }
      return null;
    case "food_cost_pct":
      // Compute from fb_cost_of_sales / fb_revenue if available
      if (kpi.fb_cost_of_sales != null && kpi.fb_revenue != null && kpi.fb_revenue > 0) {
        return Math.round((kpi.fb_cost_of_sales / kpi.fb_revenue) * 10000);
      }
      return null;
    default:
      return null;
  }
}

/* -- Pace logic ----------------------------------------------------------- */

type PaceStatus = "AHEAD" | "ON TRACK" | "BEHIND" | "AT RISK";

function getPaceStatus(
  actual: number,
  target: number,
  inverse: boolean,
): PaceStatus {
  if (target === 0) return "ON TRACK";
  if (inverse) {
    // Lower is better (labor %, food cost %)
    const ratio = (actual - target) / Math.abs(target);
    if (actual <= target) return "AHEAD";
    if (ratio <= 0.05) return "ON TRACK";
    if (ratio <= 0.15) return "BEHIND";
    return "AT RISK";
  }
  // Higher is better
  const ratio = (target - actual) / Math.abs(target);
  if (actual >= target) return "AHEAD";
  if (ratio <= 0.05) return "ON TRACK";
  if (ratio <= 0.15) return "BEHIND";
  return "AT RISK";
}

function paceColors(status: PaceStatus) {
  switch (status) {
    case "AHEAD":
    case "ON TRACK":
      return { text: "text-positive-700", bg: "bg-positive-50", stroke: "#10b981" };
    case "BEHIND":
      return { text: "text-warning-700", bg: "bg-warning-50", stroke: "#f59e0b" };
    case "AT RISK":
      return { text: "text-negative-700", bg: "bg-negative-50", stroke: "#ef4444" };
  }
}

/* -- Circular SVG Gauge --------------------------------------------------- */

function CircularGauge({
  percentage,
  strokeColor,
}: {
  percentage: number;
  strokeColor: string;
}) {
  const r = 15.5;
  const circumference = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(100, percentage));
  const dashArray = `${(clamped / 100) * circumference} ${circumference}`;

  return (
    <div className="relative w-20 h-20 flex-shrink-0">
      <svg viewBox="0 0 36 36" className="w-20 h-20 -rotate-90">
        <circle
          cx="18"
          cy="18"
          r={r}
          fill="none"
          strokeWidth="3"
          stroke="#e2e8f0"
        />
        <circle
          cx="18"
          cy="18"
          r={r}
          fill="none"
          strokeWidth="3"
          stroke={strokeColor}
          strokeDasharray={dashArray}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-bold text-surface-900">
          {Math.round(clamped)}%
        </span>
      </div>
    </div>
  );
}

/* -- Month names ---------------------------------------------------------- */

const MONTH_NAMES = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

/* -- Goal Edit Modal (kept from original) --------------------------------- */

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
      target_value: g.target_value / 100,
    })),
  );

  const usedCodes = new Set(drafts.map((d) => d.metric_code));
  const availableMetrics = AVAILABLE_METRICS.filter(
    (m) => !usedCodes.has(m.code),
  );

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
        target_value: Math.round(Number(d.target_value) * 100),
        period_type: "annual",
        year: new Date().getFullYear(),
      }));
    onSave(goals);
  };

  const canSave =
    drafts.length > 0 && drafts.every((d) => Number(d.target_value) > 0);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-200">
          <h2 className="text-lg font-medium text-surface-900">
            Edit Annual Goals
          </h2>
          <button
            onClick={onClose}
            className="text-surface-400 hover:text-surface-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {drafts.map((draft, idx) => {
            const def = METRIC_DEFS[draft.metric_code];
            return (
              <div
                key={draft.metric_code}
                className="flex items-center gap-3 border border-surface-200 rounded-lg p-3"
              >
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
                  {def?.format === "currency" && (
                    <span className="text-xs text-surface-500">$</span>
                  )}
                  <input
                    type="number"
                    value={draft.target_value}
                    onChange={(e) => updateTarget(idx, e.target.value)}
                    className="w-28 rounded border border-surface-200 px-2 py-1 text-xs tabular-nums"
                    placeholder={
                      def?.format === "percentage" ? "e.g. 70" : "e.g. 210"
                    }
                  />
                  {def?.format === "percentage" && (
                    <span className="text-xs text-surface-500">%</span>
                  )}
                </div>
              </div>
            );
          })}

          {availableMetrics.length > 0 && (
            <div>
              <div className="text-xs font-medium text-surface-500 mb-2 mt-4">
                Add metric:
              </div>
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
              canSave && !isSaving
                ? "bg-brand hover:bg-brand/90"
                : "bg-surface-300 cursor-not-allowed",
            )}
          >
            {isSaving ? "Saving..." : "Save Goals"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* -- Page Component ------------------------------------------------------- */

export default function GoalsPage() {
  const { selectedPropertyId } = useProperty();
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const currentYear = new Date().getFullYear();
  const now = new Date();
  const currentMonth = now.getMonth() + 1;
  const { data: goals, isLoading } = useGoals(currentYear);
  const createGoal = useCreateGoal();
  const updateGoal = useUpdateGoal();
  const deleteGoal = useDeleteGoal();

  const [selectorOpen, setSelectorOpen] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  // Date strings
  const ytdStart = `${currentYear}-01-01`;
  const ytdEnd = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;

  // Fetch YTD KPIs
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

  // Fetch monthly KPIs for drilldown
  const { data: monthlyKpis } = useQuery<Record<number, PLKPIData>>({
    queryKey: ["goals-monthly-kpis", selectedPropertyId, currentYear],
    queryFn: async () => {
      const months: Record<number, PLKPIData> = {};
      for (let m = 1; m <= Math.min(currentMonth, 12); m++) {
        const dim = new Date(currentYear, m, 0).getDate();
        const mStart = `${currentYear}-${String(m).padStart(2, "0")}-01`;
        const mEnd = `${currentYear}-${String(m).padStart(2, "0")}-${String(dim).padStart(2, "0")}`;
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

  // Compute % of year elapsed (based on day of year)
  const startOfYear = new Date(currentYear, 0, 1);
  const endOfYear = new Date(currentYear + 1, 0, 1);
  const yearElapsedPct =
    ((now.getTime() - startOfYear.getTime()) /
      (endOfYear.getTime() - startOfYear.getTime())) *
    100;

  const annualGoals = useMemo(
    () => (goals ?? []).filter((g) => g.period_type === "annual"),
    [goals],
  );

  // Auto-select first goal if none selected
  const effectiveSelected =
    selectedMetric && annualGoals.some((g) => g.metric_code === selectedMetric)
      ? selectedMetric
      : annualGoals.length > 0
        ? annualGoals[0].metric_code
        : null;

  // Build monthly breakdown for selected goal
  const monthlyBreakdown = useMemo(() => {
    if (!effectiveSelected) return [];
    const goal = annualGoals.find((g) => g.metric_code === effectiveSelected);
    if (!goal) return [];
    const def = METRIC_DEFS[goal.metric_code];
    // Rate metrics (occupancy, ADR, RevPAR, labor %, food cost %) keep the same
    // target each month. Only cumulative metrics (revenue, GOP, EBITDA) divide by 12.
    const monthlyTarget = def?.cumulative
      ? Math.round(goal.target_value / 12)
      : goal.target_value;

    const isCumulative = def?.cumulative ?? true;
    let ytdActualSum = 0;
    let ytdActualCount = 0;
    let ytdTargetSum = 0;
    let ytdTargetCount = 0;

    return Array.from({ length: 12 }, (_, i) => {
      const month = i + 1;
      const kpi = monthlyKpis?.[month];
      const actual = getActualForMetric(kpi, goal.metric_code);

      if (isCumulative) {
        ytdTargetSum += monthlyTarget;
        if (actual != null) ytdActualSum += actual;
      } else {
        // Rate metrics: YTD is the average across months with data
        ytdTargetCount++;
        if (actual != null) {
          ytdActualSum += actual;
          ytdActualCount++;
        }
      }

      const ytdActual = isCumulative
        ? ytdActualSum
        : ytdActualCount > 0
          ? Math.round(ytdActualSum / ytdActualCount)
          : 0;
      const ytdTarget = isCumulative
        ? ytdTargetSum
        : monthlyTarget; // For rate metrics, YTD target = the target itself

      return {
        month,
        actual,
        monthlyTarget,
        variance: actual != null ? actual - monthlyTarget : null,
        ytdActual: actual != null || month <= currentMonth ? ytdActual : null,
        ytdTarget,
        ytdVariance:
          actual != null || month <= currentMonth
            ? ytdActual - ytdTarget
            : null,
      };
    });
  }, [effectiveSelected, annualGoals, monthlyKpis, currentMonth, currentYear]);

  const handleSaveGoals = async (newGoals: GoalCreateInput[]) => {
    try {
      const existingByMetric = new Map(
        (goals ?? []).map((g) => [g.metric_code, g]),
      );
      const newMetrics = new Set(newGoals.map((g) => g.metric_code));

      for (const existing of goals ?? []) {
        if (!newMetrics.has(existing.metric_code)) {
          await deleteGoal.mutateAsync(existing.id);
        }
      }

      for (const g of newGoals) {
        const existing = existingByMetric.get(g.metric_code);
        if (existing) {
          if (existing.target_value !== g.target_value) {
            await updateGoal.mutateAsync({
              goalId: existing.id,
              input: { target_value: g.target_value },
            });
          }
        } else {
          await createGoal.mutateAsync(g);
        }
      }

      setSelectorOpen(false);
    } catch (err) {
      console.error("Failed to save goals:", err);
    }
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-surface-900">
            Annual Goals -- {currentYear}
          </h2>
          <p className="text-sm text-surface-500 mt-0.5">
            YTD through{" "}
            {now.toLocaleDateString("en-US", {
              month: "long",
              day: "numeric",
              year: "numeric",
            })}
          </p>
        </div>
        <button
          onClick={() => setSelectorOpen(true)}
          className="px-4 py-2 text-sm font-medium border border-surface-200 rounded-lg hover:bg-surface-50"
        >
          Edit Goals
        </button>
      </div>

      {/* Annual Goal Cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-52 bg-surface-100 rounded-xl animate-pulse"
            />
          ))}
        </div>
      ) : annualGoals.length > 0 ? (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
            {annualGoals.map((goal) => {
              const def = METRIC_DEFS[goal.metric_code];
              const format = def?.format ?? "currency";
              const inverse = def?.inverse ?? false;
              const actual = getActualForMetric(kpiData, goal.metric_code);

              // For cumulative metrics, YTD target is pro-rated by time elapsed.
              // For rate metrics, YTD target equals the annual target.
              const isCumulative = def?.cumulative ?? true;
              const ytdTarget = isCumulative
                ? Math.round(goal.target_value * (yearElapsedPct / 100))
                : goal.target_value;
              const variance =
                actual != null ? actual - ytdTarget : null;
              // % of YTD target achieved (consistent with pace badge)
              const pct =
                actual != null && ytdTarget > 0
                  ? (actual / ytdTarget) * 100
                  : 0;
              const pace =
                actual != null
                  ? getPaceStatus(actual, ytdTarget, inverse)
                  : ("ON TRACK" as PaceStatus);
              const colors = paceColors(pace);

              // Projected annual: for cumulative, extrapolate from elapsed time.
              // For rate metrics, current YTD average IS the projection.
              const projectedAnnual =
                actual != null
                  ? isCumulative && yearElapsedPct > 0
                    ? Math.round((actual / yearElapsedPct) * 100)
                    : actual
                  : null;

              const isSelected = effectiveSelected === goal.metric_code;

              // For inverse metrics, variance display is flipped
              const varianceIsGood =
                variance != null
                  ? inverse
                    ? variance <= 0
                    : variance >= 0
                  : true;

              return (
                <div
                  key={goal.id}
                  onClick={() => setSelectedMetric(goal.metric_code)}
                  className={cn(
                    "bg-white rounded-xl border p-5 cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-lg",
                    isSelected
                      ? "border-brand-500 ring-2 ring-brand-500"
                      : "border-surface-200",
                  )}
                >
                  {/* Header row */}
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-semibold text-surface-700">
                      {def?.label ?? goal.metric_code}
                    </span>
                    <span
                      className={cn(
                        "inline-flex px-2 py-0.5 rounded text-[10px] font-bold",
                        colors.text,
                        colors.bg,
                      )}
                    >
                      {pace}
                    </span>
                  </div>

                  {/* Gauge + values */}
                  <div className="flex items-center gap-4">
                    <CircularGauge
                      percentage={pct}
                      strokeColor={colors.stroke}
                    />
                    <div>
                      <div className="text-2xl font-bold text-surface-900">
                        {actual != null ? fmtValue(actual, format) : "--"}
                      </div>
                      <div className="text-xs text-surface-500">
                        Target: {fmtValue(ytdTarget, format)} YTD
                      </div>
                      {variance != null && (
                        <div
                          className={cn(
                            "text-xs font-medium mt-0.5",
                            varianceIsGood
                              ? "text-positive-700"
                              : colors.text,
                          )}
                        >
                          {fmtVariance(
                            inverse ? -variance : variance,
                            format,
                          )}{" "}
                          {varianceIsGood ? "ahead of pace" : "behind pace"}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Footer: Annual Target + Projected */}
                  <div className="mt-3 pt-3 border-t border-surface-100">
                    <div className="flex justify-between text-xs">
                      <span className="text-surface-500">Annual Target</span>
                      <span className="font-medium">
                        {inverse ? "< " : ""}
                        {fmtValue(goal.target_value, format)}
                      </span>
                    </div>
                    <div className="flex justify-between text-xs mt-1">
                      <span className="text-surface-500">Projected Annual</span>
                      <span
                        className={cn(
                          "font-medium",
                          projectedAnnual != null
                            ? inverse
                              ? projectedAnnual <= goal.target_value
                                ? "text-positive-700"
                                : "text-negative-700"
                              : projectedAnnual >= goal.target_value
                                ? "text-positive-700"
                                : "text-warning-700"
                            : "",
                        )}
                      >
                        {projectedAnnual != null
                          ? fmtValue(projectedAnnual, format)
                          : "--"}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Monthly Breakdown Table */}
          {effectiveSelected && (() => {
            const goal = annualGoals.find(
              (g) => g.metric_code === effectiveSelected,
            );
            if (!goal) return null;
            const def = METRIC_DEFS[goal.metric_code];
            const format = def?.format ?? "currency";
            const inverse = def?.inverse ?? false;

            // Compute YTD totals for the footer
            const isCumulative = def?.cumulative ?? true;
            let ytdActualTotal: number;
            let ytdTargetTotal: number;

            if (isCumulative) {
              ytdActualTotal = monthlyBreakdown.reduce(
                (sum, m) => sum + (m.actual ?? 0),
                0,
              );
              ytdTargetTotal = monthlyBreakdown.reduce(
                (sum, m) =>
                  m.month <= currentMonth ? sum + m.monthlyTarget : sum,
                0,
              );
            } else {
              // Rate metrics: use average of months with data
              const monthsWithData = monthlyBreakdown.filter(
                (m) => m.actual != null && m.month <= currentMonth,
              );
              ytdActualTotal =
                monthsWithData.length > 0
                  ? Math.round(
                      monthsWithData.reduce((sum, m) => sum + (m.actual ?? 0), 0) /
                        monthsWithData.length,
                    )
                  : 0;
              ytdTargetTotal = goal.target_value; // Rate target is the same all year
            }

            const overallPace = getPaceStatus(
              ytdActualTotal,
              ytdTargetTotal,
              inverse,
            );
            const overallColors = paceColors(overallPace);

            // Projected annual (for rate metrics, projected = current average)
            const projectedAnnual = isCumulative
              ? yearElapsedPct > 0
                ? Math.round((ytdActualTotal / yearElapsedPct) * 100)
                : null
              : ytdActualTotal > 0
                ? ytdActualTotal
                : null;

            return (
              <div className="bg-white rounded-xl border border-surface-200 overflow-hidden">
                <div className="px-5 py-4 border-b border-surface-100 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-surface-700">
                      Monthly Breakdown -- {def?.label ?? goal.metric_code}
                    </h3>
                    <p className="text-xs text-surface-500 mt-0.5">
                      Annual Target: {fmtValue(goal.target_value, format)}
                      {projectedAnnual != null && (
                        <>
                          {" "}
                          | Projected: {fmtValue(projectedAnnual, format)}
                        </>
                      )}
                    </p>
                  </div>
                </div>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-surface-50 border-b border-surface-200">
                      <th className="text-left py-2.5 px-4 font-semibold text-surface-500">
                        Month
                      </th>
                      <th className="text-right py-2.5 px-4 font-semibold text-surface-500">
                        Actual
                      </th>
                      <th className="text-right py-2.5 px-4 font-semibold text-surface-500">
                        Monthly Target
                      </th>
                      <th className="text-right py-2.5 px-4 font-semibold text-surface-500">
                        Variance
                      </th>
                      <th className="text-right py-2.5 px-4 font-semibold text-surface-500">
                        YTD Actual
                      </th>
                      <th className="text-right py-2.5 px-4 font-semibold text-surface-500">
                        YTD Target
                      </th>
                      <th className="text-right py-2.5 px-4 font-semibold text-surface-500">
                        YTD Variance
                      </th>
                      <th className="text-right py-2.5 px-4 font-semibold text-surface-500">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-100">
                    {monthlyBreakdown.map((row) => {
                      const isCurrent = row.month === currentMonth;
                      const isFuture = row.month > currentMonth;
                      const isPast = row.month < currentMonth;

                      const varianceBadge = (v: number | null) => {
                        if (v == null) return "--";
                        const isGood = inverse ? v <= 0 : v >= 0;
                        return (
                          <span
                            className={cn(
                              "inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium",
                              isGood
                                ? "text-positive-700 bg-positive-50"
                                : "text-negative-700 bg-negative-50",
                            )}
                          >
                            {fmtVariance(v, format)}
                          </span>
                        );
                      };

                      let status: React.ReactNode;
                      if (isCurrent) {
                        status = (
                          <span className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-bold text-brand-700 bg-brand-50">
                            IN PROGRESS
                          </span>
                        );
                      } else if (isFuture) {
                        status = (
                          <span className="text-[10px] text-surface-400">
                            UPCOMING
                          </span>
                        );
                      } else {
                        // Past month
                        const beat =
                          row.variance != null
                            ? inverse
                              ? row.variance <= 0
                              : row.variance >= 0
                            : false;
                        status = (
                          <span
                            className={cn(
                              "inline-flex px-1.5 py-0.5 rounded text-[10px] font-bold",
                              beat
                                ? "text-positive-700 bg-positive-50"
                                : "text-negative-700 bg-negative-50",
                            )}
                          >
                            {beat ? "BEAT" : "MISS"}
                          </span>
                        );
                      }

                      return (
                        <tr
                          key={row.month}
                          className={cn(
                            isCurrent && "bg-brand-50/30 hover:bg-brand-50/50",
                            isFuture && "text-surface-400",
                            isPast && "hover:bg-surface-50",
                          )}
                        >
                          <td
                            className={cn(
                              "py-2.5 px-4 font-medium",
                              isCurrent && "font-bold text-brand-700",
                            )}
                          >
                            {MONTH_NAMES[row.month - 1]}
                            {isCurrent && " (MTD)"}
                          </td>
                          <td
                            className={cn(
                              "py-2.5 px-4 text-right",
                              isCurrent && "font-bold text-brand-700",
                              isPast && "font-semibold",
                              isFuture && "italic",
                            )}
                          >
                            {row.actual != null
                              ? fmtValue(row.actual, format)
                              : "--"}
                          </td>
                          <td className="py-2.5 px-4 text-right text-surface-600">
                            {fmtValue(row.monthlyTarget, format)}
                          </td>
                          <td className="py-2.5 px-4 text-right">
                            {isFuture ? "--" : varianceBadge(row.variance)}
                          </td>
                          <td
                            className={cn(
                              "py-2.5 px-4 text-right",
                              isCurrent && "font-bold text-brand-700",
                              isPast && "font-semibold",
                              isFuture && "italic",
                            )}
                          >
                            {row.ytdActual != null && !isFuture
                              ? fmtValue(row.ytdActual, format)
                              : "--"}
                          </td>
                          <td className="py-2.5 px-4 text-right text-surface-600">
                            {isFuture
                              ? fmtValue(row.ytdTarget, format)
                              : fmtValue(row.ytdTarget, format)}
                          </td>
                          <td className="py-2.5 px-4 text-right">
                            {isFuture
                              ? "--"
                              : varianceBadge(row.ytdVariance)}
                          </td>
                          <td className="py-2.5 px-4 text-right">{status}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot>
                    <tr className="bg-surface-900 text-white font-bold">
                      <td className="py-3 px-4">Annual Total</td>
                      <td className="py-3 px-4 text-right">--</td>
                      <td className="py-3 px-4 text-right">
                        {fmtValue(goal.target_value, format)}
                      </td>
                      <td className="py-3 px-4 text-right">--</td>
                      <td className="py-3 px-4 text-right">
                        {fmtValue(ytdActualTotal, format)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {fmtValue(ytdTargetTotal, format)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {(() => {
                          const ytdVar = ytdActualTotal - ytdTargetTotal;
                          const isFavorable = inverse ? ytdVar <= 0 : ytdVar >= 0;
                          return (
                            <span
                              className="inline-flex px-1.5 py-0.5 rounded text-[10px]"
                              style={{
                                color: isFavorable ? "#a7f3d0" : "#fecaca",
                                background: "rgba(255,255,255,0.1)",
                              }}
                            >
                              {fmtVariance(ytdVar, format)}
                            </span>
                          );
                        })()}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span
                          className={cn(
                            "inline-flex px-1.5 py-0.5 rounded text-[10px]",
                          )}
                          style={{
                            color:
                              overallPace === "AHEAD" ||
                              overallPace === "ON TRACK"
                                ? "#a7f3d0"
                                : overallPace === "BEHIND"
                                  ? "#fde68a"
                                  : "#fecaca",
                            background: "rgba(255,255,255,0.1)",
                          }}
                        >
                          {overallPace}
                        </span>
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            );
          })()}
        </>
      ) : (
        <div className="rounded-lg border border-surface-200 bg-white p-8 text-center text-sm text-surface-500">
          No goals set yet. Click &quot;Edit Goals&quot; to get started.
        </div>
      )}

      <GoalEditModal
        isOpen={selectorOpen}
        onClose={() => setSelectorOpen(false)}
        existingGoals={annualGoals}
        onSave={handleSaveGoals}
        isSaving={
          createGoal.isPending ||
          updateGoal.isPending ||
          deleteGoal.isPending
        }
      />
    </div>
  );
}
