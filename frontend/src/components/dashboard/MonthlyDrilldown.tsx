"use client";

import { MonthlyRing } from "./MonthlyRing";
import type { MonthlyGoalData, GoalDisplayFormat, GoalComparisonType } from "@/types/goals";

interface MonthlyDrilldownProps {
  monthlyData: MonthlyGoalData[];
  format: GoalDisplayFormat;
  comparisonType: GoalComparisonType;
  isOpen: boolean;
}

export function MonthlyDrilldown({
  monthlyData,
  format,
  comparisonType,
  isOpen,
}: MonthlyDrilldownProps) {
  return (
    <div
      className="overflow-hidden transition-all duration-200 ease-in-out"
      style={{ maxHeight: isOpen ? 400 : 0 }}
    >
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-2 mb-4">
        <div className="grid grid-cols-4 gap-3">
          {monthlyData.map((md) => (
            <MonthlyRing
              key={md.month}
              month={md.month}
              status={md.status}
              actual={md.actual}
              target={md.target}
              percentOfGoal={md.percent_of_goal}
              format={format}
              comparisonType={comparisonType}
              isOverridden={md.is_overridden}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
