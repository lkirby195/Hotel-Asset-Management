"use client";

import { useState, useMemo } from "react";
import { Search, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { MonthlyTargetEditor } from "./MonthlyTargetEditor";
import type { GoalInput, AvailableMetric, GoalDisplayFormat, GoalComparisonType } from "@/types/goals";

// TODO: Replace with useAvailableMetrics() hook when API is ready
const MOCK_AVAILABLE_METRICS: AvailableMetric[] = [
  { line_item_id: "li-revpar", name: "RevPAR", code: "revpar", display_format: "currency", suggested_direction: "gte" },
  { line_item_id: "li-adr", name: "ADR", code: "adr", display_format: "currency", suggested_direction: "gte" },
  { line_item_id: "li-occupancy", name: "Occupancy", code: "occupancy_pct", display_format: "percentage", suggested_direction: "gte" },
  { line_item_id: "li-total-revenue", name: "Total Revenue", code: "total_revenue", display_format: "currency", suggested_direction: "gte" },
  { line_item_id: "li-rooms-revenue", name: "Room Revenue", code: "rooms_revenue", display_format: "currency", suggested_direction: "gte" },
  { line_item_id: "li-food-revenue", name: "Food Revenue", code: "fb_revenue", display_format: "currency", suggested_direction: "gte" },
  { line_item_id: "li-gop-margin", name: "GOP Margin", code: "gop_margin", display_format: "percentage", suggested_direction: "gte" },
  { line_item_id: "li-labor-cost", name: "Labor Cost %", code: "labor_cost_pct", display_format: "percentage", suggested_direction: "lte" },
  { line_item_id: "li-noi", name: "Net Operating Income", code: "net_operating_income", display_format: "currency", suggested_direction: "gte" },
  { line_item_id: "li-ebitda", name: "EBITDA", code: "ebitda", display_format: "currency", suggested_direction: "gte" },
  { line_item_id: "li-spa-revenue", name: "Spa Revenue", code: "spa_revenue", display_format: "currency", suggested_direction: "gte" },
  { line_item_id: "li-golf-revenue", name: "Golf Revenue", code: "golf_revenue", display_format: "currency", suggested_direction: "gte" },
];

interface SelectedGoal {
  line_item_id: string;
  name: string;
  display_format: GoalDisplayFormat;
  annual_target: number;
  comparison_type: GoalComparisonType;
  monthly_targets: { month: number; value: number; isOverridden: boolean }[];
  showMonthly: boolean;
}

interface GoalSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (goals: GoalInput[]) => void;
  currentGoals?: GoalInput[];
}

function makeDefaultMonthly(annualTarget: number): { month: number; value: number; isOverridden: boolean }[] {
  const perMonth = Math.round(annualTarget / 12);
  return Array.from({ length: 12 }, (_, i) => ({
    month: i + 1,
    value: perMonth,
    isOverridden: false,
  }));
}

export function GoalSelector({ isOpen, onClose, onSave }: GoalSelectorProps) {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<SelectedGoal[]>([]);

  const filteredMetrics = useMemo(() => {
    const selectedIds = new Set(selected.map((s) => s.line_item_id));
    return MOCK_AVAILABLE_METRICS.filter(
      (m) =>
        !selectedIds.has(m.line_item_id) &&
        m.name.toLowerCase().includes(search.toLowerCase())
    );
  }, [search, selected]);

  const addMetric = (metric: AvailableMetric) => {
    if (selected.length >= 5) return;
    setSelected((prev) => [
      ...prev,
      {
        line_item_id: metric.line_item_id,
        name: metric.name,
        display_format: metric.display_format,
        annual_target: 0,
        comparison_type: metric.suggested_direction,
        monthly_targets: makeDefaultMonthly(0),
        showMonthly: false,
      },
    ]);
  };

  const removeMetric = (lineItemId: string) => {
    setSelected((prev) => prev.filter((s) => s.line_item_id !== lineItemId));
  };

  const updateTarget = (lineItemId: string, value: number) => {
    setSelected((prev) =>
      prev.map((s) =>
        s.line_item_id === lineItemId
          ? { ...s, annual_target: value, monthly_targets: s.monthly_targets.some((m) => m.isOverridden) ? s.monthly_targets : makeDefaultMonthly(value) }
          : s
      )
    );
  };

  const updateDirection = (lineItemId: string, direction: GoalComparisonType) => {
    setSelected((prev) =>
      prev.map((s) =>
        s.line_item_id === lineItemId ? { ...s, comparison_type: direction } : s
      )
    );
  };

  const toggleMonthly = (lineItemId: string) => {
    setSelected((prev) =>
      prev.map((s) =>
        s.line_item_id === lineItemId ? { ...s, showMonthly: !s.showMonthly } : s
      )
    );
  };

  const updateMonthlyTarget = (lineItemId: string, month: number, value: number) => {
    setSelected((prev) =>
      prev.map((s) =>
        s.line_item_id === lineItemId
          ? {
              ...s,
              monthly_targets: s.monthly_targets.map((mt) =>
                mt.month === month ? { ...mt, value, isOverridden: true } : mt
              ),
            }
          : s
      )
    );
  };

  const resetMonthlyTargets = (lineItemId: string) => {
    setSelected((prev) =>
      prev.map((s) =>
        s.line_item_id === lineItemId
          ? { ...s, monthly_targets: makeDefaultMonthly(s.annual_target) }
          : s
      )
    );
  };

  const handleSave = () => {
    const goals: GoalInput[] = selected.map((s, i) => ({
      line_item_id: s.line_item_id,
      annual_target: s.annual_target,
      comparison_type: s.comparison_type,
      display_order: i + 1,
      monthly_overrides: s.monthly_targets
        .filter((mt) => mt.isOverridden)
        .map((mt) => ({ month: mt.month, target_value: mt.value })),
    }));
    onSave(goals);
    onClose();
  };

  const canSave = selected.length === 5 && selected.every((s) => s.annual_target > 0);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Edit Annual Goals</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2.5 top-2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search metrics..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-md border border-gray-200 pl-9 pr-3 py-1.5 text-sm"
            />
          </div>

          {/* Selected */}
          <div>
            <div className="text-xs font-medium text-gray-500 mb-2">
              Selected ({selected.length}/5):
            </div>
            {selected.length === 0 ? (
              <div className="text-xs text-gray-400 py-2">No metrics selected. Choose up to 5 below.</div>
            ) : (
              <div className="space-y-2">
                {selected.map((s) => (
                  <div key={s.line_item_id} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => removeMetric(s.line_item_id)}
                        className="text-gray-400 hover:text-red-500 shrink-0"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                      <span className="text-sm font-medium text-gray-900 flex-1">{s.name}</span>
                      <div className="flex items-center gap-2">
                        <label className="text-xs text-gray-500">Target:</label>
                        <input
                          type="number"
                          value={s.annual_target || ""}
                          onChange={(e) => updateTarget(s.line_item_id, Number(e.target.value))}
                          className="w-28 rounded border border-gray-200 px-2 py-1 text-xs tabular-nums"
                          placeholder={s.display_format === "percentage" ? "e.g. 3800" : "e.g. 185000"}
                        />
                      </div>
                      <div className="flex items-center gap-0.5">
                        <button
                          onClick={() => updateDirection(s.line_item_id, "gte")}
                          className={cn(
                            "px-2 py-0.5 text-xs rounded-l-full border",
                            s.comparison_type === "gte"
                              ? "bg-brand text-white border-brand"
                              : "bg-white text-gray-500 border-gray-200"
                          )}
                        >
                          &ge;
                        </button>
                        <button
                          onClick={() => updateDirection(s.line_item_id, "lte")}
                          className={cn(
                            "px-2 py-0.5 text-xs rounded-r-full border",
                            s.comparison_type === "lte"
                              ? "bg-brand text-white border-brand"
                              : "bg-white text-gray-500 border-gray-200"
                          )}
                        >
                          &le;
                        </button>
                      </div>
                    </div>
                    <button
                      onClick={() => toggleMonthly(s.line_item_id)}
                      className="text-xs text-brand hover:underline mt-1.5"
                    >
                      {s.showMonthly ? "Hide monthly targets" : "Edit monthly targets"}
                    </button>
                    {s.showMonthly && (
                      <MonthlyTargetEditor
                        annualTarget={s.annual_target}
                        monthlyTargets={s.monthly_targets}
                        onChange={(month, value) => updateMonthlyTarget(s.line_item_id, month, value)}
                        onReset={() => resetMonthlyTargets(s.line_item_id)}
                        format={s.display_format}
                      />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Available metrics */}
          {selected.length < 5 && (
            <div>
              <div className="text-xs font-medium text-gray-500 mb-2">Available metrics:</div>
              <div className="border border-gray-200 rounded-lg divide-y divide-gray-100 max-h-48 overflow-y-auto">
                {filteredMetrics.map((metric) => (
                  <button
                    key={metric.line_item_id}
                    onClick={() => addMetric(metric)}
                    className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 text-left"
                  >
                    <span className="h-4 w-4 rounded border border-gray-300 shrink-0" />
                    {metric.name}
                  </button>
                ))}
                {filteredMetrics.length === 0 && (
                  <div className="px-3 py-3 text-xs text-gray-400 text-center">No matching metrics</div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-gray-200">
          <button
            onClick={onClose}
            className="rounded-md px-4 py-1.5 text-sm text-gray-600 border border-gray-200 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!canSave}
            className={cn(
              "rounded-md px-4 py-1.5 text-sm text-white",
              canSave ? "bg-brand hover:bg-brand/90" : "bg-gray-300 cursor-not-allowed"
            )}
          >
            Save Goals
          </button>
        </div>
      </div>
    </div>
  );
}
