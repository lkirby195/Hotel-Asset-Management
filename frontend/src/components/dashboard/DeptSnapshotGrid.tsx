"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { createApiClient } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/formatters";
import { Skeleton } from "@/components/ui/skeleton";
import type { DeptSnapshotCard, DeptSnapshotResponse } from "@/types/dashboard";
import type { ApiResponse } from "@/types/api";

interface DeptSnapshotGridProps {
  propertyId: string;
}

const DEPT_ROUTE_MAP: Record<string, string> = {
  Rooms: "rooms",
  "F&B": "fb",
  Golf: "golf",
  "Mountain Ops": "mountain-ops",
  Spa: "spa",
  Retail: "retail",
};

function VarianceBadge({ pct }: { pct: number | null }) {
  if (pct === null) return null;
  const color = pct >= 0 ? "text-favorable" : "text-unfavorable";
  const label = pct >= 0 ? `+${pct.toFixed(1)}%` : `(${Math.abs(pct).toFixed(1)}%)`;
  return (
    <span className={cn("text-xs font-medium", color)}>{label}</span>
  );
}

function SnapshotCard({ card, onClick }: { card: DeptSnapshotCard; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="bg-white border border-gray-200 rounded-lg p-4 text-left hover:border-gray-300 hover:shadow-sm transition-all space-y-2 w-full"
    >
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {card.dept_name}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-xl font-semibold tabular-nums text-gray-900">
          {formatCurrency(card.revenue)}
        </span>
        <VarianceBadge pct={card.variance_pct} />
      </div>
      <div className="space-y-1 pt-1 border-t border-gray-100">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500">{card.kpi1_label}</span>
          <span className="font-medium text-gray-700 tabular-nums">{card.kpi1_value}</span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500">{card.kpi2_label}</span>
          <span className="font-medium text-gray-700 tabular-nums">{card.kpi2_value}</span>
        </div>
      </div>
    </button>
  );
}

function DeptSnapshotSkeleton() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="bg-white border border-gray-200 rounded-lg p-4 space-y-2">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-6 w-24" />
          <div className="space-y-1 pt-1 border-t border-gray-100">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-full" />
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
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-sm text-gray-500">
        Failed to load department snapshots.
      </div>
    );
  }

  const visibleCards = data?.cards.filter((c) => c.has_data) ?? [];

  if (visibleCards.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-sm text-gray-500">
        No department data available for this period.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
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
