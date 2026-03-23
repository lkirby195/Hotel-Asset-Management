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
  formatInteger,
  formatVarianceInteger,
} from "@/lib/formatters";
import { Skeleton } from "@/components/ui/skeleton";
import type { YesterdayKPI, YesterdayResponse } from "@/types/dashboard";
import type { ApiResponse } from "@/types/api";

interface YesterdayKPIsProps {
  propertyId: string;
}

function formatActual(kpi: YesterdayKPI): string {
  switch (kpi.unit) {
    case "currency":
      return formatCurrency(kpi.actual);
    case "percentage":
      return formatPercent(kpi.actual);
    case "integer":
      return formatInteger(kpi.actual);
  }
}

function formatVariance(value: number, unit: string): string {
  switch (unit) {
    case "currency":
      return formatVarianceCurrency(value);
    case "percentage":
      return formatVariancePercent(value);
    case "integer":
      return formatVarianceInteger(value);
    default:
      return String(value);
  }
}

function formatCompare(value: number, unit: string): string {
  switch (unit) {
    case "currency":
      return formatCurrency(value);
    case "percentage":
      return formatPercent(value);
    case "integer":
      return formatInteger(value);
    default:
      return String(value);
  }
}

function varianceColor(value: number, metricName: string): string {
  if (value === 0) return "text-gray-500";
  // Labor is an expense — lower is favorable
  const isExpense = metricName === "Total Labor";
  const isFavorable = isExpense ? value < 0 : value > 0;
  return isFavorable ? "text-favorable" : "text-unfavorable";
}

function VarianceBadge({
  label,
  variance,
  pct,
  unit,
  metricName,
}: {
  label: string;
  variance: number;
  pct: number | null;
  unit: string;
  metricName: string;
}) {
  const color = varianceColor(variance, metricName);
  return (
    <div className="flex items-center gap-1 text-xs">
      <span className="text-gray-400">{label}</span>
      <span className={cn("font-medium", color)}>
        {formatVariance(variance, unit)}
      </span>
      {pct !== null && (
        <span className={cn(color)}>({pct > 0 ? "+" : ""}{pct.toFixed(1)}%)</span>
      )}
    </div>
  );
}

function KPICard({ kpi }: { kpi: YesterdayKPI }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-2">
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {kpi.metric_name}
      </div>
      <div className="text-2xl font-semibold tabular-nums text-gray-900">
        {formatActual(kpi)}
      </div>
      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Budget: {formatCompare(kpi.budget, kpi.unit)}</span>
        </div>
        <VarianceBadge
          label="vs Budget"
          variance={kpi.variance_budget}
          pct={kpi.variance_budget_pct}
          unit={kpi.unit}
          metricName={kpi.metric_name}
        />
        <VarianceBadge
          label="vs STLY"
          variance={kpi.variance_stly}
          pct={kpi.variance_stly_pct}
          unit={kpi.unit}
          metricName={kpi.metric_name}
        />
      </div>
    </div>
  );
}

function YesterdayKPIsSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="bg-white border border-gray-200 rounded-lg p-4 space-y-2">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-7 w-24" />
          <Skeleton className="h-3 w-28" />
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-3 w-24" />
        </div>
      ))}
    </div>
  );
}

export function YesterdayKPIs({ propertyId }: YesterdayKPIsProps) {
  const { getToken } = useAuth();
  const apiClient = createApiClient(getToken);

  const { data, isLoading, error } = useQuery<YesterdayResponse>({
    queryKey: ["dashboard", "yesterday", propertyId],
    queryFn: async () => {
      const resp = await apiClient.get<ApiResponse<YesterdayResponse>>(
        `/dashboard/yesterday/${propertyId}`
      );
      return resp.data.data;
    },
    enabled: !!propertyId,
  });

  if (isLoading) return <YesterdayKPIsSkeleton />;

  if (error) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-sm text-gray-500">
        Failed to load yesterday&apos;s performance.
      </div>
    );
  }

  if (!data || data.kpis.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-sm text-gray-500">
        No data available for yesterday.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="text-xs text-gray-500">
        {new Date(data.date + "T00:00:00").toLocaleDateString("en-US", {
          weekday: "long",
          month: "long",
          day: "numeric",
          year: "numeric",
        })}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {data.kpis.map((kpi) => (
          <KPICard key={kpi.metric_name} kpi={kpi} />
        ))}
      </div>
    </div>
  );
}
