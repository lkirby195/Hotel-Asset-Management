import type { GoalsResponse, GoalWithProgress, MonthlyGoalData } from "@/types/goals";

function makeMonthlyData(
  annualTarget: number,
  actuals: (number | null)[],
  currentMonth: number
): MonthlyGoalData[] {
  const monthlyTarget = Math.round(annualTarget / 12);
  return Array.from({ length: 12 }, (_, i) => {
    const month = i + 1;
    const actual = actuals[i] ?? null;
    let status: MonthlyGoalData["status"] = "not_started";
    if (month < currentMonth) status = "completed";
    else if (month === currentMonth) status = "current";
    return {
      month,
      target: monthlyTarget,
      is_overridden: false,
      actual,
      percent_of_goal: actual !== null && monthlyTarget > 0 ? actual / monthlyTarget : null,
      status,
    };
  });
}

// Current month is March (3)
const CURRENT_MONTH = 3;

export const MOCK_GOALS: GoalWithProgress[] = [
  {
    id: "goal-1",
    line_item_id: "li-revpar",
    line_item_name: "RevPAR",
    display_format: "currency",
    comparison_type: "gte",
    display_order: 1,
    annual_target: 2220000, // $22,200 annual in cents
    ytd_actual: 560550,
    ytd_target: 555000,
    percent_of_annual: 0.2525,
    trend_7d: "up",
    monthly_data: makeMonthlyData(2220000, [189200, 182400, 188950, null, null, null, null, null, null, null, null, null], CURRENT_MONTH),
  },
  {
    id: "goal-2",
    line_item_id: "li-gop-margin",
    line_item_name: "GOP Margin",
    display_format: "percentage",
    comparison_type: "gte",
    display_order: 2,
    annual_target: 3800, // 38.0% stored as basis points
    ytd_actual: 3920,
    ytd_target: 3800,
    percent_of_annual: 1.032,
    trend_7d: "up",
    monthly_data: makeMonthlyData(3800, [4020, 3810, 3930, null, null, null, null, null, null, null, null, null], CURRENT_MONTH),
  },
  {
    id: "goal-3",
    line_item_id: "li-labor-cost",
    line_item_name: "Labor Cost %",
    display_format: "percentage",
    comparison_type: "lte",
    display_order: 3,
    annual_target: 3150, // 31.5%
    ytd_actual: 3080,
    ytd_target: 3150,
    percent_of_annual: 0.978,
    trend_7d: "flat",
    monthly_data: makeMonthlyData(3150, [3020, 3120, 3100, null, null, null, null, null, null, null, null, null], CURRENT_MONTH),
  },
  {
    id: "goal-4",
    line_item_id: "li-total-revenue",
    line_item_name: "Total Revenue",
    display_format: "currency",
    comparison_type: "gte",
    display_order: 4,
    annual_target: 240000000, // $2.4M annual
    ytd_actual: 54735000,
    ytd_target: 60000000,
    percent_of_annual: 0.228,
    trend_7d: "up",
    monthly_data: makeMonthlyData(240000000, [19200000, 18085000, 17450000, null, null, null, null, null, null, null, null, null], CURRENT_MONTH),
  },
  {
    id: "goal-5",
    line_item_id: "li-food-revenue",
    line_item_name: "Food Revenue",
    display_format: "currency",
    comparison_type: "gte",
    display_order: 5,
    annual_target: 30000000, // $300K annual
    ytd_actual: 6840000,
    ytd_target: 7500000,
    percent_of_annual: 0.228,
    trend_7d: "down",
    monthly_data: makeMonthlyData(30000000, [2520000, 2480000, 1840000, null, null, null, null, null, null, null, null, null], CURRENT_MONTH),
  },
];

export const MOCK_GOALS_RESPONSE: GoalsResponse = {
  goals: MOCK_GOALS,
  as_of_date: "2026-03-21",
};
