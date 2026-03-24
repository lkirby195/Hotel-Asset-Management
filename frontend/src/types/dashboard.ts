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

// ── Forward Look / OTB ─────────────────────────────────────────

export interface OTBSummaryCard {
  window_name: string;
  date_start: string;
  date_end: string;
  nights: number;
  otb_revenue: number;   // cents
  otb_occupancy: number;
  otb_adr: number;       // cents
  stly_revenue: number;  // cents
  vs_stly_revenue: number; // cents
  vs_stly_pct: number | null;
  budget_remaining: number | null; // cents
  pickup_7day: number | null;      // cents
}

export interface OTBDailyRow {
  date: string;
  day_of_week: string;
  transient_rooms: number;
  group_rooms: number;
  total_rooms: number;
  occupancy: number;
  adr: number;       // cents
  revenue: number;   // cents
  stly_rooms: number;
  stly_revenue: number; // cents
  vs_stly_pct: number | null;
}

export interface ForwardLookResponse {
  property_id: string;
  property_name: string;
  as_of_date: string;
  available_rooms_per_night: number;
  summary_cards: OTBSummaryCard[];
  daily_detail: OTBDailyRow[];
}
