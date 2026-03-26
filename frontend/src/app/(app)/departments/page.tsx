"use client";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import {
  BedDouble,
  UtensilsCrossed,
  Flag,
  ShoppingBag,
  Mountain,
  Sparkles,
  MoreHorizontal,
} from "lucide-react";
import { createApiClient } from "@/lib/api-client";
import { useProperty } from "@/providers/property-provider";
import { formatCurrency } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import type { ApiResponse } from "@/types/api";
import type { DeptSnapshotResponse, DeptSnapshotCard } from "@/types/dashboard";
import type { LucideIcon } from "lucide-react";

const DEPT_ICON: Record<string, LucideIcon> = {
  Rooms: BedDouble,
  "F&B": UtensilsCrossed,
  "Food & Beverage": UtensilsCrossed,
  Golf: Flag,
  "Mountain Ops": Mountain,
  Spa: Sparkles,
  Retail: ShoppingBag,
};

const DEPT_SLUG: Record<string, string> = {
  Rooms: "rooms",
  "F&B": "fb",
  "Food & Beverage": "fb",
  Golf: "golf",
  "Mountain Ops": "mountain",
  Spa: "spa",
  Retail: "retail",
};

export default function DepartmentsIndex() {
  const { selectedPropertyId, properties } = useProperty();
  const { getToken } = useAuth();
  const router = useRouter();
  const api = createApiClient(getToken);
  const property = properties.find((p) => p.id === selectedPropertyId);

  const { data, isLoading } = useQuery<DeptSnapshotResponse>({
    queryKey: ["dashboard", "dept-snapshots", selectedPropertyId],
    queryFn: async () => {
      const resp = await api.get<ApiResponse<DeptSnapshotResponse>>(
        `/dashboard/dept-snapshots/${selectedPropertyId}`,
      );
      return resp.data.data;
    },
    enabled: !!selectedPropertyId,
  });

  if (!selectedPropertyId) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="rounded-xl border border-surface-200 bg-white p-8 text-center text-sm text-surface-500">
          Select a property to view departments.
        </div>
      </div>
    );
  }

  const cards = data?.cards?.filter((c: DeptSnapshotCard) => c.has_data) ?? [];

  return (
    <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
      <div>
        <h2 className="text-xl font-bold text-surface-900">Departments</h2>
        <p className="text-sm text-surface-500 mt-0.5">
          {property?.name ?? "Property"} -- Month-to-Date Performance
        </p>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-5">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-surface-200 p-5 h-40 animate-pulse"
            />
          ))}
        </div>
      ) : cards.length === 0 ? (
        <div className="rounded-xl border border-surface-200 bg-white p-8 text-center text-sm text-surface-500">
          No department data available for this property.
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-5">
          {cards.map((card: DeptSnapshotCard) => {
            const Icon = DEPT_ICON[card.dept_name] ?? MoreHorizontal;
            const slug =
              DEPT_SLUG[card.dept_name] ?? card.dept_name.toLowerCase();
            return (
              <button
                key={card.dept_name}
                onClick={() => router.push(`/departments/${slug}`)}
                className="bg-white rounded-xl border border-surface-200 p-5 text-left hover:shadow-lg hover:-translate-y-0.5 transition-all group"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-lg bg-brand-50 flex items-center justify-center">
                    <Icon className="w-5 h-5 text-brand-700" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-surface-900 group-hover:text-brand-700 transition-colors">
                      {card.dept_name}
                    </h3>
                  </div>
                </div>
                <div className="flex items-baseline justify-between">
                  <div>
                    <div className="text-[10px] font-medium text-surface-400 uppercase tracking-wide">
                      MTD Revenue
                    </div>
                    <div className="text-lg font-bold text-surface-900 tabular-nums">
                      {formatCurrency(card.revenue)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[10px] font-medium text-surface-400 uppercase tracking-wide">
                      vs Budget
                    </div>
                    <span
                      className={cn(
                        "inline-flex px-1.5 py-0.5 rounded text-xs font-medium tabular-nums",
                        (card.variance_pct ?? 0) >= 0
                          ? "text-positive-700 bg-positive-50"
                          : "text-negative-700 bg-negative-50",
                      )}
                    >
                      {(card.variance_pct ?? 0) >= 0 ? "+" : ""}
                      {card.variance_pct != null
                        ? `${card.variance_pct.toFixed(1)}%`
                        : "--"}
                    </span>
                  </div>
                </div>
                <div className="mt-2 pt-2 border-t border-surface-100 space-y-1">
                  {card.kpi1_label && (
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-surface-400">
                        {card.kpi1_label}
                      </span>
                      <span className="text-xs font-semibold text-surface-700 tabular-nums">
                        {card.kpi1_value}
                      </span>
                    </div>
                  )}
                  {card.kpi2_label && (
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-surface-400">
                        {card.kpi2_label}
                      </span>
                      <span className="text-xs font-semibold text-surface-700 tabular-nums">
                        {card.kpi2_value}
                      </span>
                    </div>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
