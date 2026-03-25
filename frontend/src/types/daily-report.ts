export interface DualPanelRow {
  line_name: string;
  daily_actual: number | null;
  daily_forecast: number | null;
  daily_stly: number | null;
  daily_vs_forecast: number | null;
  daily_vs_stly: number | null;
  mtd_actual: number | null;
  mtd_budget: number | null;
  mtd_stly: number | null;
  mtd_fcst_lock: number | null;
  mtd_vs_budget: number | null;
  mtd_vs_stly: number | null;
  is_header: boolean;
  is_total: boolean;
  indent: number;
  unit: "currency" | "percent" | "number" | "pts";
}

export interface DailyReportSection {
  section_name: string;
  rows: DualPanelRow[];
}

export interface DailyReportResponse {
  property_id: string;
  property_name: string;
  report_date: string;
  available_rooms: number;
  sections: Record<string, DailyReportSection[]>;
}
