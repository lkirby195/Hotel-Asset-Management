import type { PeriodSelection } from './reports';

export interface PortfolioPropertyRow {
  property_id: string;
  property_name: string;
  revpar: number;
  adr: number;
  occupancy_percent: number;
  total_revenue: number;
  gop_margin_percent: number;
  labor_cost_percent: number;
  pace_vs_stly_percent: number;
  budget_variance_percent: number;
}

export interface PortfolioSummary {
  total_revenue: number;
  avg_revpar: number;
  avg_occupancy: number;
  avg_gop_margin: number;
  property_count: number;
  period: PeriodSelection;
  rows: PortfolioPropertyRow[];
}
