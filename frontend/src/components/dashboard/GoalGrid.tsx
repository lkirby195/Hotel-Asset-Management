"use client";

import { GoalGauge } from "./GoalGauge";

// Placeholder goals until the API endpoint exists
const PLACEHOLDER_GOALS = [
  { label: "RevPAR", current_value: 18742, target_value: 18500, percent_of_goal: 1.013, format: "currency" as const, comparison_type: "gte" as const },
  { label: "Total Revenue", current_value: 158930088, target_value: 155000000, percent_of_goal: 1.025, format: "currency" as const, comparison_type: "gte" as const },
  { label: "Occupancy", current_value: 0.784, target_value: 0.80, percent_of_goal: 0.98, format: "percentage" as const, comparison_type: "gte" as const },
  { label: "GOP Margin", current_value: 0.392, target_value: 0.40, percent_of_goal: 0.98, format: "percentage" as const, comparison_type: "gte" as const },
  { label: "Labor Cost %", current_value: 0.305, target_value: 0.32, percent_of_goal: 1.049, format: "percentage" as const, comparison_type: "lte" as const },
];

export function GoalGrid() {
  const firstRow = PLACEHOLDER_GOALS.slice(0, 3);
  const secondRow = PLACEHOLDER_GOALS.slice(3, 5);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        {firstRow.map((goal) => (
          <GoalGauge key={goal.label} {...goal} />
        ))}
      </div>
      {secondRow.length > 0 && (
        <div className="grid grid-cols-2 gap-4 mx-auto" style={{ maxWidth: "66%" }}>
          {secondRow.map((goal) => (
            <GoalGauge key={goal.label} {...goal} />
          ))}
        </div>
      )}
    </div>
  );
}
