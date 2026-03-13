"use client";

import { cn } from "@/lib/utils";
import { formatVarianceCurrency, formatVariancePercent, getVarianceColor } from "@/lib/formatters";

interface VarianceDisplayProps {
  dollar: number;
  percent: number;
  data_type: "revenue" | "expense" | "metric" | "percentage";
  show_dollar?: boolean;
  show_percent?: boolean;
}

export function VarianceDisplay({
  dollar,
  percent,
  data_type,
  show_dollar = true,
  show_percent = true,
}: VarianceDisplayProps) {
  const color = getVarianceColor(dollar, data_type);

  return (
    <span className={cn("tabular-nums", color)}>
      {show_dollar && formatVarianceCurrency(dollar)}
      {show_dollar && show_percent && " "}
      {show_percent && (
        <span className="text-xs opacity-70">
          ({formatVariancePercent(percent)})
        </span>
      )}
    </span>
  );
}
