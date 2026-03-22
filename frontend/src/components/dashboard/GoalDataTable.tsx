"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, ChevronUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatCurrency, formatVarianceCurrency } from "@/lib/formatters";
import type { GoalWithProgress, MonthlyGoalData, GoalDisplayFormat } from "@/types/goals";

const MONTH_SHORT = [
  "", "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const TrendIcon = {
  up: ChevronUp,
  down: TrendingDown,
  flat: Minus,
};

interface GoalDataTableProps {
  goals: GoalWithProgress[];
}

function formatValue(value: number, format: GoalDisplayFormat): string {
  if (format === "percentage") return `${(value / 100).toFixed(1)}%`;
  return formatCurrency(value);
}

function formatVariance(value: number, format: GoalDisplayFormat): string {
  if (format === "percentage") {
    const pp = (value / 100).toFixed(1);
    if (value > 0) return `+${pp}pp`;
    if (value < 0) return `(${Math.abs(value / 100).toFixed(1)}pp)`;
    return `${pp}pp`;
  }
  return formatVarianceCurrency(value);
}

export function GoalDataTable({ goals }: GoalDataTableProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table className="w-full">
        <thead>
          <tr className="border-b-2 border-gray-200 bg-gray-100 text-xs font-medium uppercase tracking-wide text-gray-500">
            <th className="px-3 py-2.5 text-left" style={{ minWidth: 200 }}>Metric</th>
            <th className="px-3 py-2.5 text-right whitespace-nowrap" style={{ minWidth: 100 }}>Annual Target</th>
            <th className="px-3 py-2.5 text-right whitespace-nowrap" style={{ minWidth: 100 }}>YTD Actual</th>
            <th className="px-3 py-2.5 text-right whitespace-nowrap" style={{ minWidth: 100 }}>YTD Target</th>
            <th className="px-3 py-2.5 text-right whitespace-nowrap" style={{ minWidth: 80 }}>% of Annual</th>
            <th className="px-3 py-2.5 text-center whitespace-nowrap" style={{ minWidth: 60 }}>Trend</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {goals.map((goal) => {
            const isExpanded = expandedIds.has(goal.id);
            const Icon = TrendIcon[goal.trend_7d];
            const pctColor = goal.comparison_type === "lte"
              ? (goal.percent_of_annual <= 1 ? "text-favorable" : "text-unfavorable")
              : (goal.percent_of_annual >= 1 ? "text-favorable" : "text-unfavorable");

            return (
              <GoalAccordionRow
                key={goal.id}
                goal={goal}
                isExpanded={isExpanded}
                onToggle={() => toggleExpand(goal.id)}
                trendIcon={Icon}
                pctColor={pctColor}
              />
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function GoalAccordionRow({
  goal,
  isExpanded,
  onToggle,
  trendIcon: Icon,
  pctColor,
}: {
  goal: GoalWithProgress;
  isExpanded: boolean;
  onToggle: () => void;
  trendIcon: typeof ChevronUp;
  pctColor: string;
}) {
  return (
    <>
      <tr
        className="cursor-pointer hover:bg-gray-50 transition-colors font-medium"
        onClick={onToggle}
      >
        <td className="px-3 py-2 text-sm text-gray-900">
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 shrink-0 text-gray-400" />
            ) : (
              <ChevronRight className="h-4 w-4 shrink-0 text-gray-400" />
            )}
            {goal.line_item_name}
          </div>
        </td>
        <td className="px-3 py-2 text-sm text-right tabular-nums whitespace-nowrap">
          {formatValue(goal.annual_target, goal.display_format)}
        </td>
        <td className="px-3 py-2 text-sm text-right tabular-nums whitespace-nowrap">
          {formatValue(goal.ytd_actual, goal.display_format)}
        </td>
        <td className="px-3 py-2 text-sm text-right tabular-nums whitespace-nowrap text-gray-500">
          {formatValue(goal.ytd_target, goal.display_format)}
        </td>
        <td className={cn("px-3 py-2 text-sm text-right tabular-nums whitespace-nowrap", pctColor)}>
          {(goal.percent_of_annual * 100).toFixed(1)}%
        </td>
        <td className="px-3 py-2 text-center">
          <Icon
            className={cn(
              "inline-block h-3 w-3",
              goal.trend_7d === "up" && "text-favorable",
              goal.trend_7d === "down" && "text-unfavorable",
              goal.trend_7d === "flat" && "text-gray-400"
            )}
          />
        </td>
      </tr>

      {/* Monthly sub-rows */}
      {isExpanded &&
        goal.monthly_data.map((md) => (
          <MonthlySubRow
            key={md.month}
            data={md}
            format={goal.display_format}
            comparisonType={goal.comparison_type}
          />
        ))}
    </>
  );
}

function MonthlySubRow({
  data,
  format,
  comparisonType,
}: {
  data: MonthlyGoalData;
  format: GoalDisplayFormat;
  comparisonType: "gte" | "lte";
}) {
  const isNotStarted = data.status === "not_started";
  const isCurrent = data.status === "current";
  const variance = data.actual !== null ? data.actual - data.target : null;

  const varianceColor =
    variance !== null
      ? comparisonType === "lte"
        ? variance <= 0 ? "text-favorable" : "text-unfavorable"
        : variance >= 0 ? "text-favorable" : "text-unfavorable"
      : "";

  const pctOfGoal = data.percent_of_goal;
  const pctColor =
    pctOfGoal !== null
      ? comparisonType === "lte"
        ? pctOfGoal <= 1 ? "text-favorable" : "text-unfavorable"
        : pctOfGoal >= 1 ? "text-favorable" : "text-unfavorable"
      : "";

  return (
    <tr
      className={cn(
        "text-sm",
        isCurrent && "border-l-2 border-brand",
        isNotStarted && "text-gray-400"
      )}
    >
      <td className="px-3 py-1.5 pl-10">
        <span className={cn(data.is_overridden && "text-brand")}>
          {MONTH_SHORT[data.month]}
        </span>
      </td>
      <td className={cn("px-3 py-1.5 text-right tabular-nums whitespace-nowrap", data.is_overridden && "text-brand")}>
        {formatValue(data.target, format)}
      </td>
      <td className="px-3 py-1.5 text-right tabular-nums whitespace-nowrap">
        {data.actual !== null ? formatValue(data.actual, format) : "--"}
      </td>
      <td className={cn("px-3 py-1.5 text-right tabular-nums whitespace-nowrap", varianceColor)}>
        {variance !== null ? formatVariance(variance, format) : "--"}
      </td>
      <td className={cn("px-3 py-1.5 text-right tabular-nums whitespace-nowrap", pctColor)}>
        {pctOfGoal !== null ? `${(pctOfGoal * 100).toFixed(1)}%` : "--"}
      </td>
      <td />
    </tr>
  );
}
