"use client";

import { cn } from "@/lib/utils";

export interface KpiCardProps {
  label: string;
  value: string;
  change?: {
    value: string;
    direction: "up" | "down" | "neutral";
  };
}

export function KpiCard({ label, value, change }: KpiCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-2xl font-medium tabular-nums text-gray-900">
        {value}
      </div>
      {change && (
        <div
          className={cn(
            "text-xs",
            change.direction === "up" && "text-favorable",
            change.direction === "down" && "text-unfavorable",
            change.direction === "neutral" && "text-gray-500"
          )}
        >
          {change.value}
        </div>
      )}
    </div>
  );
}
