import type { PeriodType } from './reports';

export type ComparisonType = 'gte' | 'lte';

export interface UserGoal {
  id: string;
  user_id: string;
  line_item_id: string;
  line_item_name: string;
  target_value: number;
  comparison_type: ComparisonType;
  time_period: PeriodType;
  current_value: number;
  percent_of_goal: number;
  trend_7d: 'up' | 'down' | 'flat';
}
