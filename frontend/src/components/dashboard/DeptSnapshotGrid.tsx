"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { createApiClient } from "@/lib/api-client";
import { formatCurrency } from "@/lib/formatters";
import { VarianceBadge } from "@/components/ui/variance-badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { DeptSnapshotCard, DeptSnapshotResponse } from "@/types/dashboard";
import type { ApiResponse } from "@/types/api";

interface DeptSnapshotGridProps {
  propertyId: string;
}

const DEPT_ROUTE_MAP: Record<string, string> = {
  Rooms: "rooms",
  "F&B": "fb",
  "Food & Beverage": "fb",
  Golf: "golf",
  "Mountain Ops": "mountain-ops",
  Spa: "spa",
  Retail: "retail",
};

const DEPT_EMOJI: Record<string, string> = {
  Rooms: "\uD83D\uDECF\uFE0F",
  "F&B": "\uD83C\uDF7D\uFE0F",
  "Food & Beverage": "\uD83C\uDF7D\uFE0F",
  Golf: "\u26F3",
  "Mountain Ops": "\u26F7\uFE0F",
  Spa: "\uD83D\uDC86",
  Retail: "\uD83D\uDECD\uFE0F",
};

function budgetLabel(budget: number): string {
  const dollars = Math.abs(budget) / 100;
  if (dollars >= 1_000_000) return `$${(dollars / 1_000_000).toFixed(1)}M`;
  if (dollars >= 1_000) return `$${(dollars / 1_000).toFixed(1)}K`;
  return `$${dollars.toFixed(0)}`;
}

function SnapshotCard({ card, onClick }: { card: DeptSnapshotCard; onClick: () => void }) {
  const emoji = DEPT_EMOJI[card.dept_name] ?? "";

  return (
    <button
      onClick={onClick}
      className="kpi-card bg-white rounded-xl border border-surface-200 p-4 text-left w-full cursor-pointer"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-surface-700">
          {emoji} {card.dept_name}
        </span>
        {card.variance_pct !== null && (
          <VarianceBadge
            value={card.variance_pct}
            label={`${card.variance_pct >= 0 ? "+" : ""}${card.variance_pct.toFixed(1)}%`}
            favorable={card.variance_pct >= 0}
          />
        )}
      </div>
      <div className="text-xl font-bold tabular-nums">{formatCurrency(card.revenue)}</div>
      <div className="text-xs text-surface-500">
        Revenue vs {budgetLabel(card.budget)} budget
      </div>
      <div className="mt-2 flex items-center gap-3 text-xs">
        <span className="text-surface-500">
          {card.kpi1_label}: <span className="font-medium text-surface-700">{card.kpi1_value}</span>
        </span>
        <span className="text-surface-500">
          {card.kpi2_label}: <span className="font-medium text-surface-700">{card.kpi2_value}</span>
        </span>
      </div>
    </button>
  );
}

function DeptSnapshotSkeleton() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-5">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="bg-white rounded-xl border border-surface-200 p-4 space-y-2">
          <div className="flex justify-between">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-12" />
          </div>
          <Skeleton className="h-6 w-28" />
          <Skeleton className="h-3 w-36" />
          <div className="flex gap-3 mt-2">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function DeptSnapshotGrid({ propertyId }: DeptSnapshotGridProps) {
  const { getToken } = useAuth();
  const router = useRouter();
  const apiClient = createApiClient(getToken);

  const { data, isLoading, error } = useQuery<DeptSnapshotResponse>({
    queryKey: ["dashboard", "dept-snapshots", propertyId],
    queryFn: async () => {
      const resp = await apiClient.get<ApiResponse<DeptSnapshotResponse>>(
        `/dashboard/dept-snapshots/${propertyId}`
      );
      return resp.data.data;
    },
    enabled: !!propertyId,
  });

  if (isLoading) return <DeptSnapshotSkeleton />;

  if (error) {
    return (
      <div className="rounded-xl border border-surface-200 bg-white p-6 min-h-[140px] flex items-center justify-center text-sm text-surface-500">
        Failed to load department snapshots.
      </div>
    );
  }

  const visibleCards = data?.cards.filter((c) => c.has_data) ?? [];

  if (visibleCards.length === 0) {
    return (
      <div className="rounded-xl border border-surface-200 bg-white p-6 min-h-[140px] flex items-center justify-center text-sm text-surface-500">
        No department data available for this period.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-5">
      {visibleCards.map((card) => (
        <SnapshotCard
          key={card.dept_name}
          card={card}
          onClick={() => {
            const slug = DEPT_ROUTE_MAP[card.dept_name] ?? card.dept_name.toLowerCase();
            router.push(`/departments/${slug}`);
          }}
        />
      ))}
    </div>
  );
}
