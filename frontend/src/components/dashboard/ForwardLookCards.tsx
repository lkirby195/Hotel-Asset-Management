"use client";

import { cn } from "@/lib/utils";
import {
  formatCurrency,
  formatVarianceCurrency,
} from "@/lib/formatters";
import { VarianceBadge } from "@/components/ui/variance-badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { ForwardLookResponse, OTBSummaryCard } from "@/types/dashboard";

interface ForwardLookCardsProps {
  propertyId: string;
  data?: ForwardLookResponse;
  isLoading?: boolean;
  error?: Error | null;
}

function SummaryCard({ card }: { card: OTBSummaryCard }) {
  const startDate = new Date(card.date_start + "T00:00:00");
  const endDate = new Date(card.date_end + "T00:00:00");
  const dateRange = `${startDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })} \u2013 ${endDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`;

  const stlyLabel = card.vs_stly_pct !== null
    ? `${formatVarianceCurrency(card.vs_stly_revenue)} (${card.vs_stly_pct > 0 ? "+" : ""}${card.vs_stly_pct.toFixed(1)}%)`
    : formatVarianceCurrency(card.vs_stly_revenue);

  return (
    <div className="kpi-card bg-white rounded-xl border border-surface-200 p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs font-semibold text-surface-500 uppercase tracking-wider">
          {card.window_name}
        </div>
        <span className="text-xs text-surface-400">
          {card.nights} nights
        </span>
      </div>

      <div className="space-y-3">
        <div className="flex justify-between items-baseline">
          <span className="text-sm text-surface-600">OTB Room Revenue</span>
          <span className="text-lg font-bold tabular-nums">{formatCurrency(card.otb_revenue)}</span>
        </div>
        <div className="flex justify-between items-baseline">
          <span className="text-sm text-surface-600">OTB Occupancy</span>
          <span className="text-lg font-bold tabular-nums">
            {(card.otb_occupancy * 100).toFixed(1)}%
          </span>
        </div>
        <div className="flex justify-between items-baseline">
          <span className="text-sm text-surface-600">OTB ADR</span>
          <span className="text-lg font-bold tabular-nums">{formatCurrency(card.otb_adr)}</span>
        </div>

        <div className="border-t border-surface-100 pt-2 mt-2">
          <div className="flex justify-between items-center">
            <span className="text-xs text-surface-500">vs STLY OTB</span>
            <VarianceBadge
              value={card.vs_stly_revenue}
              label={stlyLabel}
              favorable={card.vs_stly_revenue > 0}
            />
          </div>

          {card.budget_remaining !== null && (
            <div className="flex justify-between items-center mt-1">
              <span className="text-xs text-surface-500">Budget Remaining</span>
              <VarianceBadge
                value={-card.budget_remaining}
                label={`${formatVarianceCurrency(-card.budget_remaining)} gap`}
                favorable={card.budget_remaining <= 0}
              />
            </div>
          )}

          {card.pickup_7day !== null && (
            <div className="flex justify-between items-center mt-1">
              <span className="text-xs text-surface-500">Pickup (last 7 days)</span>
              <VarianceBadge
                value={card.pickup_7day}
                label={formatVarianceCurrency(card.pickup_7day)}
                favorable={card.pickup_7day > 0}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function CardsSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="bg-white rounded-xl border border-surface-200 p-5 space-y-3">
          <div className="flex justify-between">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-16" />
          </div>
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, j) => (
              <div key={j} className="flex justify-between">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-5 w-20" />
              </div>
            ))}
          </div>
          <div className="border-t border-surface-100 pt-2 space-y-2">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-full" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function ForwardLookCards({ propertyId, data, isLoading, error }: ForwardLookCardsProps) {
  if (isLoading) return <CardsSkeleton />;

  if (error) {
    return (
      <div className="rounded-xl border border-surface-200 bg-white p-6 min-h-[140px] flex items-center justify-center text-sm text-surface-500">
        Failed to load forward look data.
      </div>
    );
  }

  if (!data || data.summary_cards.length === 0) {
    return (
      <div className="rounded-xl border border-surface-200 bg-white p-6 min-h-[140px] flex items-center justify-center text-sm text-surface-500">
        No OTB data available.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
      {data.summary_cards.map((card) => (
        <SummaryCard key={card.window_name} card={card} />
      ))}
    </div>
  );
}
