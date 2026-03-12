export const PERIODS = [
  { value: "mtd" as const, label: "MTD" },
  { value: "qtd" as const, label: "QTD" },
  { value: "ytd" as const, label: "YTD" },
  { value: "t28" as const, label: "T28" },
  { value: "weekly" as const, label: "Weekly" },
  { value: "custom" as const, label: "Custom" },
] as const;

export const ROLE_LABELS: Record<string, string> = {
  admin: "Admin",
  executive: "Executive",
  operator: "Operator",
  manager: "Manager",
};
