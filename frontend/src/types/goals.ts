export type GoalComparisonType = "gte" | "lte";
export type GoalDisplayFormat = "currency" | "percentage" | "integer" | "decimal";
export type MonthStatus = "completed" | "current" | "not_started";
export type TrendDirection = "up" | "down" | "flat";

export interface GoalWithProgress {
  id: string;
  line_item_id: string;
  line_item_name: string;
  display_format: GoalDisplayFormat;
  comparison_type: GoalComparisonType;
  display_order: number;
  annual_target: number;
  ytd_actual: number;
  ytd_target: number;
  percent_of_annual: number;
  trend_7d: TrendDirection;
  monthly_data: MonthlyGoalData[];
}

export interface MonthlyGoalData {
  month: number;
  target: number;
  is_overridden: boolean;
  actual: number | null;
  percent_of_goal: number | null;
  status: MonthStatus;
}

export interface GoalInput {
  line_item_id: string;
  annual_target: number;
  comparison_type: GoalComparisonType;
  display_order: number;
  monthly_overrides?: { month: number; target_value: number }[];
}

export interface AvailableMetric {
  line_item_id: string;
  name: string;
  code: string;
  display_format: GoalDisplayFormat;
  suggested_direction: GoalComparisonType;
}

export interface GoalsResponse {
  goals: GoalWithProgress[];
  as_of_date: string;
}
