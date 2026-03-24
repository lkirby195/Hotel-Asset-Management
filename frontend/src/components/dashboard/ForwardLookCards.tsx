"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  formatCurrency,
  formatVarianceCurrency,
  formatPercent,
} from "@/lib/formatters";
import { Skeleton } from "@/components/ui/skeleton";
import type { ForwardLookResponse, OTBSummaryCard } from "@/types/dashboard";
import type { ApiResponse } from "@/types/api";

interface ForwardLookCardsProps {
  propertyId: string;
  data?: ForwardLookResponse;
  isLoading?: boolean;
  error?: Error | null;
}

function varianceColor(value: number): string {
  if (value === 0) return "text-gray-500";
  return value > 0 ? "text-favorable" : "text-unfavorable";
}

function SummaryCard({ card }: { card: OTBSummaryCard }) {
  const startDate = new Date(card.date_start + "T00:00:00");
  const endDate = new Date(card.date_end + "T00:00:00");
  const dateRange = `${startDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })} – ${endDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-3">
      <div>
        <h3 className="text-sm font-semibold text-gray-900">{card.window_name}</h3>
        <p className="text-xs text-gray-500">{dateRange} &middot; {card.nights} nights</p>
      </div>

      {/* Primary OTB metrics */}
      <div className="grid grid-cols-3 gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-wide text-gray-500">OTB Revenue</p>
          <p className="text-sm font-semibold text-gray-900 tabular-nums">
            {formatCurrency(card.otb_revenue)}
          </p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wide text-gray-500">OTB Occ</p>
          <p className="text-sm font-semibold text-gray-900 tabular-nums">
            {formatPercent(card.otb_occupancy)}
          </p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wide text-gray-500">OTB ADR</p>
          <p className="text-sm font-semibold text-gray-900 tabular-nums">
            {formatCurrency(card.otb_adr)}
          </p>
        </div>
      </div>

      {/* Comparison metrics */}
      <div className="border-t border-gray-100 pt-2 space-y-1.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500">vs STLY</span>
          <span className={cn("font-medium tabular-nums", varianceColor(card.vs_stly_revenue))}>
            {formatVarianceCurrency(card.vs_stly_revenue)}
            {card.vs_stly_pct !== null && (
              <span className="ml-1 text-[10px]">
                ({card.vs_stly_pct > 0 ? "+" : ""}{card.vs_stly_pct.toFixed(1)}%)
              </span>
            )}
          </span>
        </div>

        {card.budget_remaining !== null && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-500">Budget Gap</span>
            <span className={cn("font-medium tabular-nums", varianceColor(-card.budget_remaining))}>
              {formatVarianceCurrency(-card.budget_remaining)}
            </span>
          </div>
        )}

        {card.pickup_7day !== null && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-500">7-Day Pickup</span>
            <span className={cn("font-medium tabular-nums", varianceColor(card.pickup_7day))}>
              {formatVarianceCurrency(card.pickup_7day)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function CardsSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="rounded-lg border border-gray-200 bg-white p-4 space-y-3">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-3 w-32" />
          <div className="grid grid-cols-3 gap-3">
            {Array.from({ length: 3 }).map((_, j) => (
              <div key={j} className="space-y-1">
                <Skeleton className="h-2.5 w-12" />
                <Skeleton className="h-4 w-16" />
              </div>
            ))}
          </div>
          <div className="space-y-1.5 pt-2">
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
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-sm text-gray-500">
        Failed to load forward look data.
      </div>
    );
  }

  if (!data || data.summary_cards.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-sm text-gray-500">
        No OTB data available.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {data.summary_cards.map((card) => (
        <SummaryCard key={card.window_name} card={card} />
      ))}
    </div>
  );
}
