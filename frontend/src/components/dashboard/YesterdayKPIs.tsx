"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import {
  formatCurrency,
  formatVarianceCurrency,
  formatPercent,
  formatVariancePercent,
  formatInteger,
  formatVarianceInteger,
} from "@/lib/formatters";
import { KpiCard } from "@/components/ui/kpi-card";
import { VarianceBadge } from "@/components/ui/variance-badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { YesterdayKPI, YesterdayResponse } from "@/types/dashboard";
import type { ApiResponse } from "@/types/api";

interface YesterdayKPIsProps {
  propertyId: string;
}

function fmtActual(kpi: YesterdayKPI): string {
  switch (kpi.unit) {
    case "currency":
      return formatCurrency(kpi.actual);
    case "percentage":
      return formatPercent(kpi.actual);
    case "integer":
      return formatInteger(kpi.actual);
  }
}

function fmtCompare(value: number, unit: string): string {
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

function fmtVariance(value: number, unit: string): string {
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

function isExpenseMetric(name: string): boolean {
  return name === "Total Labor";
}

function isFavorable(value: number, metricName: string): boolean {
  return isExpenseMetric(metricName) ? value < 0 : value > 0;
}

function KPICardItem({ kpi }: { kpi: YesterdayKPI }) {
  const budgetLabel = `Budget: ${fmtCompare(kpi.budget, kpi.unit)}`;

  return (
    <KpiCard label={kpi.metric_name} value={fmtActual(kpi)} subtitle={budgetLabel}>
      {kpi.variance_budget !== 0 && (
        <VarianceBadge
          value={kpi.variance_budget}
          label={`${fmtVariance(kpi.variance_budget, kpi.unit)} vs Bgt`}
          favorable={isFavorable(kpi.variance_budget, kpi.metric_name)}
        />
      )}
      {kpi.variance_stly !== 0 && (
        <VarianceBadge
          value={kpi.variance_stly}
          label={`${fmtVariance(kpi.variance_stly, kpi.unit)} vs STLY`}
          favorable={isFavorable(kpi.variance_stly, kpi.metric_name)}
        />
      )}
    </KpiCard>
  );
}

function YesterdayKPIsSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="bg-white rounded-xl border border-surface-200 p-4 space-y-2">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-7 w-24" />
          <Skeleton className="h-3 w-28" />
          <Skeleton className="h-3 w-32" />
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
      <div className="rounded-xl border border-surface-200 bg-white p-6 text-center text-sm text-surface-500">
        Failed to load yesterday&apos;s performance.
      </div>
    );
  }

  if (!data || data.kpis.length === 0) {
    return (
      <div className="rounded-xl border border-surface-200 bg-white p-6 text-center text-sm text-surface-500">
        No data available for yesterday.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {data.kpis.map((kpi) => (
        <KPICardItem key={kpi.metric_name} kpi={kpi} />
      ))}
    </div>
  );
}
