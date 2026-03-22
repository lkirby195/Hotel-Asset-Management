import type { PeriodType, ComparisonType } from "@/types/reports";
import type { DepartmentType } from "@/types/users";

export const PLATFORM_NAME = "APEX";
export const PLATFORM_ACCENT = "hospitality";

export const PERIODS: { value: PeriodType; label: string }[] = [
  { value: "mtd", label: "MTD" },
  { value: "qtd", label: "QTD" },
  { value: "ytd", label: "YTD" },
  { value: "t28", label: "T28" },
  { value: "weekly", label: "Weekly" },
  { value: "custom", label: "Custom" },
];

export const COMPARISON_OPTIONS: { value: ComparisonType; label: string }[] = [
  { value: "budget", label: "Budget" },
  { value: "forecast_lock", label: "Fcst Lock" },
  { value: "stly", label: "STLY" },
];

export const DEFAULT_COMPARISONS: ComparisonType[] = ["budget", "stly"];

export const ROLE_LABELS: Record<string, string> = {
  admin: "Admin",
  executive: "Executive",
  operator: "Operator",
  manager: "Manager",
};

export const DEPARTMENT_LABELS: Record<DepartmentType, string> = {
  rooms: "Rooms",
  fb: "Food & Beverage",
  spa: "Spa",
  golf: "Golf",
  retail: "Retail",
  mountain: "Mountain Operations",
  other: "Other Operated Departments",
};
