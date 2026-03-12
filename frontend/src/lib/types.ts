export interface Property {
  id: string;
  name: string;
  code: string;
  timezone: string;
  is_active: boolean;
  departments: Department[];
}

export interface Department {
  id: string;
  type: string;
  name: string;
  is_active: boolean;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: "admin" | "executive" | "operator" | "manager";
  is_active: boolean;
  property_ids: string[];
}

export interface ReportLineItem {
  id: string;
  code: string;
  name: string;
  parent_id: string | null;
  is_summary: boolean;
  data_type: "revenue" | "expense";
  sort_order: number;
  depth: number;
  actual: number; // cents
  budget: number; // cents
  variance_dollars: number;
  variance_pct: number | null;
  prior_year_actual: number | null;
  py_variance_dollars: number | null;
  py_variance_pct: number | null;
}

export interface InterMonthReport {
  property_id: string;
  property_name: string;
  period: string;
  start_date: string;
  end_date: string;
  lines: ReportLineItem[];
}

export interface APIResponse<T> {
  data: T;
  meta?: Record<string, unknown>;
  errors?: { code: string; message: string; field?: string }[];
}

export type Period = "mtd" | "qtd" | "ytd" | "t28" | "custom" | "weekly";
