"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  formatCurrency,
  formatVarianceCurrency,
  formatPercent,
  formatVariancePercent,
  formatPercentagePoints,
} from "@/lib/formatters";
import { Skeleton } from "@/components/ui/skeleton";
import type { MTDPaceRow, MTDPaceResponse } from "@/types/dashboard";
import type { ApiResponse } from "@/types/api";

interface MTDPaceTableProps {
  propertyId: string;
}

function formatActual(row: MTDPaceRow): string {
  return row.unit === "currency" ? formatCurrency(row.actual) : formatPercent(row.actual);
}

function formatComparison(value: number, unit: string): string {
  return unit === "currency" ? formatCurrency(value) : formatPercent(value);
}

function formatVariance(value: number, unit: string): string {
  // Percentage metrics use percentage points (pp) for variance, not relative %
  return unit === "currency" ? formatVarianceCurrency(value) : formatPercentagePoints(value);
}

function varianceColor(value: number, metricName: string): string {
  if (value === 0) return "text-gray-500";
  const isExpense = metricName === "Total Labor" || metricName === "Labor % of Revenue";
  const isFavorable = isExpense ? value < 0 : value > 0;
  return isFavorable ? "text-favorable" : "text-unfavorable";
}

function VarianceBadge({ value, pct, unit, metricName }: {
  value: number;
  pct: number | null;
  unit: string;
  metricName: string;
}) {
  const color = varianceColor(value, metricName);
  return (
    <span className={cn("text-xs font-medium whitespace-nowrap", color)}>
      {formatVariance(value, unit)}
      {pct !== null && (
        <span className="ml-0.5 text-[10px]">({pct > 0 ? "+" : ""}{pct.toFixed(1)}%)</span>
      )}
    </span>
  );
}

function MTDPaceTableSkeleton() {
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {Array.from({ length: 8 }).map((_, i) => (
                <th key={i} className="px-3 py-2.5">
                  <Skeleton className="h-3 w-16" />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 7 }).map((_, i) => (
              <tr key={i} className="border-b border-gray-100">
                {Array.from({ length: 8 }).map((_, j) => (
                  <td key={j} className="px-3 py-2.5">
                    <Skeleton className="h-3 w-16" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function MTDPaceTable({ propertyId }: MTDPaceTableProps) {
  const { getToken } = useAuth();
  const apiClient = createApiClient(getToken);

  const { data, isLoading, error } = useQuery<MTDPaceResponse>({
    queryKey: ["dashboard", "mtd-pace", propertyId],
    queryFn: async () => {
      const resp = await apiClient.get<ApiResponse<MTDPaceResponse>>(
        `/dashboard/mtd-pace/${propertyId}`
      );
      return resp.data.data;
    },
    enabled: !!propertyId,
  });

  if (isLoading) return <MTDPaceTableSkeleton />;

  if (error) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-sm text-gray-500">
        Failed to load MTD pace data.
      </div>
    );
  }

  if (!data || data.rows.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-sm text-gray-500">
        No MTD data available.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="text-xs text-gray-500">
        {new Date(data.period_start + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" })}
        {" – "}
        {new Date(data.period_end + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
        <span className="ml-2 text-gray-400">
          ({data.days_elapsed} of {data.days_in_month} days)
        </span>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wide">
                <th className="px-3 py-2.5 text-left">Metric</th>
                <th className="px-3 py-2.5 text-right">Actual</th>
                <th className="px-3 py-2.5 text-right">Budget</th>
                <th className="px-3 py-2.5 text-right">STLY</th>
                <th className="px-3 py-2.5 text-right">Fcst Lock</th>
                <th className="px-3 py-2.5 text-right">vs Budget</th>
                <th className="px-3 py-2.5 text-right">vs STLY</th>
                <th className="px-3 py-2.5 text-right">vs Fcst</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row) => (
                <tr key={row.metric_name} className="border-b border-gray-100 last:border-b-0 hover:bg-gray-50/50">
                  <td className="px-3 py-2.5 font-medium text-gray-900 whitespace-nowrap">
                    {row.metric_name}
                  </td>
                  <td className="px-3 py-2.5 text-right tabular-nums font-semibold text-gray-900">
                    {formatActual(row)}
                  </td>
                  <td className="px-3 py-2.5 text-right tabular-nums text-gray-600">
                    {formatComparison(row.budget, row.unit)}
                  </td>
                  <td className="px-3 py-2.5 text-right tabular-nums text-gray-600">
                    {formatComparison(row.stly, row.unit)}
                  </td>
                  <td className="px-3 py-2.5 text-right tabular-nums text-gray-600">
                    {formatComparison(row.forecast_lock, row.unit)}
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <VarianceBadge value={row.vs_budget} pct={row.vs_budget_pct} unit={row.unit} metricName={row.metric_name} />
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <VarianceBadge value={row.vs_stly} pct={row.vs_stly_pct} unit={row.unit} metricName={row.metric_name} />
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <span className={cn("text-xs font-medium whitespace-nowrap", varianceColor(row.vs_forecast, row.metric_name))}>
                      {formatVariance(row.vs_forecast, row.unit)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
