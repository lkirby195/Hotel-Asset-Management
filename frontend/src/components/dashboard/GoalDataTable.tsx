"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

const PLACEHOLDER_DATA = [
  { metric: "RevPAR", current: "$187.42", target: "$185.00", pctOfGoal: 101.3, trend: "up" as const },
  { metric: "Total Revenue", current: "$1,589K", target: "$1,550K", pctOfGoal: 102.5, trend: "up" as const },
  { metric: "Occupancy", current: "78.4%", target: "80.0%", pctOfGoal: 98.0, trend: "flat" as const },
  { metric: "GOP Margin", current: "39.2%", target: "40.0%", pctOfGoal: 98.0, trend: "down" as const },
  { metric: "Labor Cost %", current: "30.5%", target: "\u226432.0%", pctOfGoal: 104.9, trend: "up" as const },
];

const TrendIcon = {
  up: TrendingUp,
  down: TrendingDown,
  flat: Minus,
};

export function GoalDataTable() {
  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table className="w-full">
        <thead>
          <tr className="border-b bg-surface text-xs font-medium uppercase tracking-wide text-gray-500">
            <th className="px-3 py-3 text-left">Metric</th>
            <th className="px-3 py-3 text-right">Current</th>
            <th className="px-3 py-3 text-right">Target</th>
            <th className="px-3 py-3 text-right">% of Goal</th>
            <th className="px-3 py-3 text-center">7d Trend</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {PLACEHOLDER_DATA.map((row) => {
            const Icon = TrendIcon[row.trend];
            return (
              <tr
                key={row.metric}
                className="cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <td className="px-3 py-2 text-sm font-medium text-gray-900">
                  {row.metric}
                </td>
                <td className="px-3 py-2 text-sm text-right tabular-nums text-gray-900">
                  {row.current}
                </td>
                <td className="px-3 py-2 text-sm text-right tabular-nums text-gray-500">
                  {row.target}
                </td>
                <td
                  className={cn(
                    "px-3 py-2 text-sm text-right tabular-nums",
                    row.pctOfGoal >= 100 ? "text-favorable" : "text-unfavorable"
                  )}
                >
                  {row.pctOfGoal.toFixed(1)}%
                </td>
                <td className="px-3 py-2 text-center">
                  <Icon
                    className={cn(
                      "inline-block h-4 w-4",
                      row.trend === "up" && "text-favorable",
                      row.trend === "down" && "text-unfavorable",
                      row.trend === "flat" && "text-gray-400"
                    )}
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
