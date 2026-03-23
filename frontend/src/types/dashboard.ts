export interface YesterdayKPI {
  metric_name: string;
  actual: number;
  budget: number;
  stly: number;
  variance_budget: number;
  variance_budget_pct: number | null;
  variance_stly: number;
  variance_stly_pct: number | null;
  unit: 'currency' | 'percentage' | 'integer';
}

export interface YesterdayResponse {
  property_id: string;
  property_name: string;
  date: string;
  kpis: YesterdayKPI[];
}

export interface MTDPaceRow {
  metric_name: string;
  actual: number;
  budget: number;
  stly: number;
  forecast_lock: number;
  vs_budget: number;
  vs_budget_pct: number | null;
  vs_stly: number;
  vs_stly_pct: number | null;
  vs_forecast: number;
  unit: 'currency' | 'percentage' | 'integer';
}

export interface MTDPaceResponse {
  property_id: string;
  property_name: string;
  period_start: string;
  period_end: string;
  days_elapsed: number;
  days_in_month: number;
  rows: MTDPaceRow[];
}
