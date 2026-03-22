"use client";

import { useState } from "react";
import { GoalGauge } from "./GoalGauge";
import { MonthlyDrilldown } from "./MonthlyDrilldown";
import type { GoalWithProgress } from "@/types/goals";

interface GoalGridProps {
  goals: GoalWithProgress[];
}

export function GoalGrid({ goals }: GoalGridProps) {
  const [expandedGoalId, setExpandedGoalId] = useState<string | null>(null);

  const firstRow = goals.slice(0, 3);
  const secondRow = goals.slice(3, 5);

  const toggleExpand = (id: string) => {
    setExpandedGoalId((prev) => (prev === id ? null : id));
  };

  const expandedFirstRow = firstRow.find((g) => g.id === expandedGoalId);
  const expandedSecondRow = secondRow.find((g) => g.id === expandedGoalId);

  return (
    <div className="space-y-0">
      {/* Row 1: 3 gauges */}
      <div className="grid grid-cols-3 gap-4">
        {firstRow.map((goal) => (
          <GoalGauge
            key={goal.id}
            label={goal.line_item_name}
            current_value={goal.ytd_actual}
            target_value={goal.annual_target}
            percent_of_goal={goal.percent_of_annual}
            format={goal.display_format}
            comparison_type={goal.comparison_type}
            isExpanded={expandedGoalId === goal.id}
            onClick={() => toggleExpand(goal.id)}
          />
        ))}
      </div>

      {/* Monthly drilldown for row 1 */}
      {expandedFirstRow && (
        <MonthlyDrilldown
          monthlyData={expandedFirstRow.monthly_data}
          format={expandedFirstRow.display_format}
          comparisonType={expandedFirstRow.comparison_type}
          isOpen={true}
        />
      )}

      {/* Row 2: 2 gauges centered */}
      {secondRow.length > 0 && (
        <div className="grid grid-cols-2 gap-4 mx-auto mt-4" style={{ maxWidth: "66%" }}>
          {secondRow.map((goal) => (
            <GoalGauge
              key={goal.id}
              label={goal.line_item_name}
              current_value={goal.ytd_actual}
              target_value={goal.annual_target}
              percent_of_goal={goal.percent_of_annual}
              format={goal.display_format}
              comparison_type={goal.comparison_type}
              isExpanded={expandedGoalId === goal.id}
              onClick={() => toggleExpand(goal.id)}
            />
          ))}
        </div>
      )}

      {/* Monthly drilldown for row 2 */}
      {expandedSecondRow && (
        <MonthlyDrilldown
          monthlyData={expandedSecondRow.monthly_data}
          format={expandedSecondRow.display_format}
          comparisonType={expandedSecondRow.comparison_type}
          isOpen={true}
        />
      )}
    </div>
  );
}
