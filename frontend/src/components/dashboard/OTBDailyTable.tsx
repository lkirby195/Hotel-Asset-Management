"use client";

import { cn } from "@/lib/utils";
import {
  formatCurrency,
  formatPercent,
  formatInteger,
} from "@/lib/formatters";
import { Skeleton } from "@/components/ui/skeleton";
import type { ForwardLookResponse, OTBDailyRow } from "@/types/dashboard";

interface OTBDailyTableProps {
  data?: ForwardLookResponse;
  isLoading?: boolean;
}

const WEEKEND_DAYS = new Set(["Sat", "Sun"]);

function isWeekend(dayOfWeek: string): boolean {
  return WEEKEND_DAYS.has(dayOfWeek);
}

function varianceColor(value: number | null): string {
  if (value === null || value === 0) return "text-gray-500";
  return value > 0 ? "text-favorable" : "text-unfavorable";
}

function OTBDailyTableSkeleton() {
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {Array.from({ length: 11 }).map((_, i) => (
                <th key={i} className="px-3 py-2.5">
                  <Skeleton className="h-3 w-14" />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 7 }).map((_, i) => (
              <tr key={i} className="border-b border-gray-100">
                {Array.from({ length: 11 }).map((_, j) => (
                  <td key={j} className="px-3 py-2.5">
                    <Skeleton className="h-3 w-14" />
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

export function OTBDailyTable({ data, isLoading }: OTBDailyTableProps) {
  if (isLoading) return <OTBDailyTableSkeleton />;

  if (!data || data.daily_detail.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-sm text-gray-500">
        No daily OTB detail available.
      </div>
    );
  }

  const rows = data.daily_detail;

  // Compute totals
  const totals = rows.reduce(
    (acc, row) => ({
      transient_rooms: acc.transient_rooms + row.transient_rooms,
      group_rooms: acc.group_rooms + row.group_rooms,
      total_rooms: acc.total_rooms + row.total_rooms,
      revenue: acc.revenue + row.revenue,
      stly_rooms: acc.stly_rooms + row.stly_rooms,
      stly_revenue: acc.stly_revenue + row.stly_revenue,
    }),
    { transient_rooms: 0, group_rooms: 0, total_rooms: 0, revenue: 0, stly_rooms: 0, stly_revenue: 0 },
  );

  const totalOcc = totals.total_rooms / (data.available_rooms_per_night * rows.length) || 0;
  const totalAdr = totals.total_rooms ? Math.round(totals.revenue / totals.total_rooms) : 0;
  const totalVsStlyPct = totals.stly_revenue
    ? Math.round((totals.revenue - totals.stly_revenue) / totals.stly_revenue * 1000) / 10
    : null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wide">
              <th className="px-3 py-2.5 text-left">Date</th>
              <th className="px-3 py-2.5 text-left">Day</th>
              <th className="px-3 py-2.5 text-right">Transient</th>
              <th className="px-3 py-2.5 text-right">Group</th>
              <th className="px-3 py-2.5 text-right">Total Rms</th>
              <th className="px-3 py-2.5 text-right">Occ %</th>
              <th className="px-3 py-2.5 text-right">ADR</th>
              <th className="px-3 py-2.5 text-right">Revenue</th>
              <th className="px-3 py-2.5 text-right">STLY Rms</th>
              <th className="px-3 py-2.5 text-right">STLY Rev</th>
              <th className="px-3 py-2.5 text-right">vs STLY</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const d = new Date(row.date + "T00:00:00");
              const dateLabel = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
              const weekend = isWeekend(row.day_of_week);

              return (
                <tr
                  key={row.date}
                  className={cn(
                    "border-b border-gray-100 last:border-b-0",
                    weekend && "bg-gray-50/60",
                  )}
                >
                  <td className="px-3 py-2 text-gray-900 whitespace-nowrap">{dateLabel}</td>
                  <td className={cn("px-3 py-2 whitespace-nowrap", weekend ? "font-medium text-gray-700" : "text-gray-500")}>
                    {row.day_of_week}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums text-gray-700">{formatInteger(row.transient_rooms)}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-gray-700">{formatInteger(row.group_rooms)}</td>
                  <td className="px-3 py-2 text-right tabular-nums font-medium text-gray-900">{formatInteger(row.total_rooms)}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-gray-700">{formatPercent(row.occupancy)}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-gray-700">{formatCurrency(row.adr)}</td>
                  <td className="px-3 py-2 text-right tabular-nums font-medium text-gray-900">{formatCurrency(row.revenue)}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-gray-500">{formatInteger(row.stly_rooms)}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-gray-500">{formatCurrency(row.stly_revenue)}</td>
                  <td className="px-3 py-2 text-right">
                    {row.vs_stly_pct !== null ? (
                      <span className={cn("text-xs font-medium tabular-nums", varianceColor(row.vs_stly_pct))}>
                        {row.vs_stly_pct > 0 ? "+" : ""}{row.vs_stly_pct.toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr className="border-t border-gray-300 bg-gray-50 font-semibold text-gray-900">
              <td className="px-3 py-2.5">Total</td>
              <td className="px-3 py-2.5" />
              <td className="px-3 py-2.5 text-right tabular-nums">{formatInteger(totals.transient_rooms)}</td>
              <td className="px-3 py-2.5 text-right tabular-nums">{formatInteger(totals.group_rooms)}</td>
              <td className="px-3 py-2.5 text-right tabular-nums">{formatInteger(totals.total_rooms)}</td>
              <td className="px-3 py-2.5 text-right tabular-nums">{formatPercent(totalOcc)}</td>
              <td className="px-3 py-2.5 text-right tabular-nums">{formatCurrency(totalAdr)}</td>
              <td className="px-3 py-2.5 text-right tabular-nums">{formatCurrency(totals.revenue)}</td>
              <td className="px-3 py-2.5 text-right tabular-nums text-gray-500">{formatInteger(totals.stly_rooms)}</td>
              <td className="px-3 py-2.5 text-right tabular-nums text-gray-500">{formatCurrency(totals.stly_revenue)}</td>
              <td className="px-3 py-2.5 text-right">
                {totalVsStlyPct !== null ? (
                  <span className={cn("text-xs font-medium tabular-nums", varianceColor(totalVsStlyPct))}>
                    {totalVsStlyPct > 0 ? "+" : ""}{totalVsStlyPct.toFixed(1)}%
                  </span>
                ) : (
                  <span className="text-xs text-gray-400">—</span>
                )}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
