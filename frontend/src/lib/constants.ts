import type { PeriodType } from "@/types/reports";
import type { DepartmentType } from "@/types/users";

export const PERIODS: { value: PeriodType; label: string }[] = [
  { value: "mtd", label: "MTD" },
  { value: "qtd", label: "QTD" },
  { value: "ytd", label: "YTD" },
  { value: "t28", label: "T28" },
  { value: "weekly", label: "Weekly" },
  { value: "custom", label: "Custom" },
];

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
