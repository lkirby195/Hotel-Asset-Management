"use client";

import { cn } from "@/lib/utils";

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

interface MonthlyTargetEditorProps {
  annualTarget: number;
  monthlyTargets: { month: number; value: number; isOverridden: boolean }[];
  onChange: (month: number, value: number) => void;
  onReset: () => void;
  format: "currency" | "percentage" | "integer" | "decimal";
}

export function MonthlyTargetEditor({
  annualTarget,
  monthlyTargets,
  onChange,
  onReset,
  format,
}: MonthlyTargetEditorProps) {
  const monthlySum = monthlyTargets.reduce((sum, m) => sum + m.value, 0);
  const diff = monthlySum - annualTarget;
  const hasDiff = Math.abs(diff) > 0;

  const formatLabel = (v: number) => {
    if (format === "percentage") return `${(v / 100).toFixed(1)}%`;
    return `$${(v / 100).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
  };

  return (
    <div className="border border-gray-200 rounded-lg p-3 mt-2 bg-gray-50">
      <div className="text-xs font-medium text-gray-700 mb-2">
        Monthly targets (Annual: {formatLabel(annualTarget)})
      </div>
      <div className="grid grid-cols-3 gap-2">
        {monthlyTargets.map((mt) => (
          <div key={mt.month} className="flex items-center gap-1.5">
            <label className="text-xs text-gray-500 w-8 shrink-0">{MONTH_LABELS[mt.month - 1]}:</label>
            <input
              type="number"
              value={mt.value}
              onChange={(e) => onChange(mt.month, Number(e.target.value))}
              className={cn(
                "w-full rounded border border-gray-200 px-2 py-1 text-xs tabular-nums",
                mt.isOverridden && "text-brand border-brand/30"
              )}
            />
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between mt-2">
        <button
          onClick={onReset}
          className="text-xs text-gray-500 hover:text-gray-700 underline"
        >
          Reset to auto-prorate
        </button>
        {hasDiff && (
          <span className="text-xs text-amber-600">
            Monthly sum: {formatLabel(monthlySum)} (diff: {diff > 0 ? "+" : ""}{formatLabel(diff)})
          </span>
        )}
      </div>
    </div>
  );
}
