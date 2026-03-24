"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  formatCurrency,
  formatVarianceCurrency,
  formatPercent,
  formatPercentagePoints,
} from "@/lib/formatters";
import { DataTable, TableHeader, Th } from "@/components/ui/data-table";
import { VarianceBadge } from "@/components/ui/variance-badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { MTDPaceRow, MTDPaceResponse } from "@/types/dashboard";
import type { ApiResponse } from "@/types/api";

interface MTDPaceTableProps {
  propertyId: string;
}

function fmtActual(row: MTDPaceRow): string {
  return row.unit === "currency" ? formatCurrency(row.actual) : formatPercent(row.actual);
}

function fmtComparison(value: number, unit: string): string {
  return unit === "currency" ? formatCurrency(value) : formatPercent(value);
}

function fmtVariance(value: number, unit: string): string {
  return unit === "currency" ? formatVarianceCurrency(value) : formatPercentagePoints(value);
}

function isExpenseMetric(name: string): boolean {
  return name === "Total Labor" || name === "Labor % of Revenue";
}

function isFavorable(value: number, metricName: string): boolean {
  if (value === 0) return true;
  return isExpenseMetric(metricName) ? value < 0 : value > 0;
}

function isHighlightRow(name: string): boolean {
  return name === "Room Revenue" || name === "Total Revenue";
}

function PaceVarianceBadge({
  value,
  pct,
  unit,
  metricName,
}: {
  value: number;
  pct: number | null;
  unit: string;
  metricName: string;
}) {
  if (value === 0 && (pct === null || pct === 0)) return <span className="text-xs text-surface-400">&mdash;</span>;
  const label =
    pct !== null && unit === "currency"
      ? `${fmtVariance(value, unit)} (${pct > 0 ? "+" : ""}${pct.toFixed(1)}%)`
      : fmtVariance(value, unit);

  return (
    <VarianceBadge
      value={value}
      label={label}
      favorable={isFavorable(value, metricName)}
    />
  );
}

function MTDPaceTableSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-surface-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-50 border-b border-surface-200">
              {Array.from({ length: 8 }).map((_, i) => (
                <th key={i} className="px-4 py-3">
                  <Skeleton className="h-3 w-16" />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 7 }).map((_, i) => (
              <tr key={i} className="border-b border-surface-100">
                {Array.from({ length: 8 }).map((_, j) => (
                  <td key={j} className="px-4 py-3">
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
      <div className="rounded-xl border border-surface-200 bg-white p-6 min-h-[140px] flex items-center justify-center text-sm text-surface-500">
        Failed to load MTD pace data.
      </div>
    );
  }

  if (!data || data.rows.length === 0) {
    return (
      <div className="rounded-xl border border-surface-200 bg-white p-6 min-h-[140px] flex items-center justify-center text-sm text-surface-500">
        No MTD data available.
      </div>
    );
  }

  return (
    <DataTable>
      <TableHeader>
        <Th align="left">Metric</Th>
        <Th>Actual</Th>
        <Th>Budget</Th>
        <Th>STLY</Th>
        <Th>Fcst Lock</Th>
        <Th>vs Budget</Th>
        <Th>vs STLY</Th>
        <Th>vs Fcst</Th>
      </TableHeader>
      <tbody className="divide-y divide-surface-100">
        {data.rows.map((row) => (
          <tr
            key={row.metric_name}
            className={cn(
              "hover:bg-surface-50",
              isHighlightRow(row.metric_name) && "bg-surface-50/50",
            )}
          >
            <td
              className={cn(
                "py-3 px-4",
                isHighlightRow(row.metric_name) ? "font-semibold" : "font-medium",
              )}
            >
              {row.metric_name}
            </td>
            <td
              className={cn(
                "py-3 px-4 text-right tabular-nums",
                isHighlightRow(row.metric_name) ? "font-bold" : "font-semibold",
              )}
            >
              {fmtActual(row)}
            </td>
            <td className="py-3 px-4 text-right tabular-nums text-surface-600">
              {fmtComparison(row.budget, row.unit)}
            </td>
            <td className="py-3 px-4 text-right tabular-nums text-surface-600">
              {fmtComparison(row.stly, row.unit)}
            </td>
            <td className="py-3 px-4 text-right tabular-nums text-surface-600">
              {fmtComparison(row.forecast_lock, row.unit)}
            </td>
            <td className="py-3 px-4 text-right">
              <PaceVarianceBadge
                value={row.vs_budget}
                pct={row.vs_budget_pct}
                unit={row.unit}
                metricName={row.metric_name}
              />
            </td>
            <td className="py-3 px-4 text-right">
              <PaceVarianceBadge
                value={row.vs_stly}
                pct={row.vs_stly_pct}
                unit={row.unit}
                metricName={row.metric_name}
              />
            </td>
            <td className="py-3 px-4 text-right">
              <PaceVarianceBadge
                value={row.vs_forecast}
                pct={null}
                unit={row.unit}
                metricName={row.metric_name}
              />
            </td>
          </tr>
        ))}
      </tbody>
    </DataTable>
  );
}
