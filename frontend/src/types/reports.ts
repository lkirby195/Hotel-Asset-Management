import type { DepartmentType } from './users';

export type PeriodType = 'mtd' | 'qtd' | 'ytd' | 't28' | 'weekly' | 'custom';

export interface PeriodSelection {
  type: PeriodType;
  start_date?: string;
  end_date?: string;
}

export interface LineItem {
  id: string;
  code: string;
  name: string;
  parent_id: string | null;
  department_type: DepartmentType | null;
  sort_order: number;
  is_summary: boolean;
  data_type: 'revenue' | 'expense' | 'metric' | 'percentage';
  has_children: boolean;
}

export interface ReportRow {
  line_item: LineItem;
  actual: number;
  budget: number;
  variance_dollar: number;
  variance_percent: number;
  prior_year_actual: number;
  py_variance_dollar: number;
  py_variance_percent: number;
  forecast?: number;
  forecast_variance_dollar?: number;
  forecast_variance_percent?: number;
}

export interface ReportData {
  property_id: string;
  property_name: string;
  period: PeriodSelection;
  as_of_date: string;
  rows: ReportRow[];
  last_synced: string;
}

export interface ChildRowsData {
  parent_line_item_id: string;
  rows: ReportRow[];
}
