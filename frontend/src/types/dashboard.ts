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
