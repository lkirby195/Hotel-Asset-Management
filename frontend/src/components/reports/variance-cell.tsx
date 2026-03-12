"use client";

import { cn, formatCurrency, formatPercent } from "@/lib/utils";

interface VarianceCellProps {
  value: number;
  percentage: number | null;
  dataType: "revenue" | "expense";
}

export function VarianceCell({ value, percentage, dataType }: VarianceCellProps) {
  // Favorable: revenue positive OR expense negative
  const isFavorable =
    dataType === "revenue" ? value >= 0 : value <= 0;

  return (
    <td
      className={cn(
        "px-3 py-2 text-right tabular-nums",
        isFavorable ? "text-green-700" : "text-red-700"
      )}
    >
      <div>{formatCurrency(value)}</div>
      {percentage !== null && (
        <div className="text-xs opacity-70">{formatPercent(percentage)}</div>
      )}
    </td>
  );
}
