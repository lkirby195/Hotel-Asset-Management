"use client";

import { cn } from "@/lib/utils";
import { formatCurrency, formatPercent } from "@/lib/formatters";
import { DataTable, TableHeader, Th } from "@/components/ui/data-table";
import { VarianceBadge } from "@/components/ui/variance-badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { ForwardLookResponse } from "@/types/dashboard";

interface OTBDailyTableProps {
  data?: ForwardLookResponse;
  isLoading?: boolean;
}

const WEEKEND_DAYS = new Set(["Fri", "Sat"]);

function OTBDailyTableSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-surface-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-surface-100">
        <Skeleton className="h-3 w-40" />
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-surface-50 border-b border-surface-200">
            {Array.from({ length: 8 }).map((_, i) => (
              <th key={i} className="px-4 py-2.5">
                <Skeleton className="h-3 w-14" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 7 }).map((_, i) => (
            <tr key={i} className="border-b border-surface-100">
              {Array.from({ length: 8 }).map((_, j) => (
                <td key={j} className="px-4 py-2.5">
                  <Skeleton className="h-3 w-14" />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function OTBDailyTable({ data, isLoading }: OTBDailyTableProps) {
  if (isLoading) return <OTBDailyTableSkeleton />;

  if (!data || data.daily_detail.length === 0) {
    return (
      <div className="rounded-xl border border-surface-200 bg-white p-6 text-center text-sm text-surface-500">
        No daily OTB detail available.
      </div>
    );
  }

  const rows = data.daily_detail;

  // Compute totals
  const totals = rows.reduce(
    (acc, row) => ({
      total_rooms: acc.total_rooms + row.total_rooms,
      revenue: acc.revenue + row.revenue,
      stly_revenue: acc.stly_revenue + row.stly_revenue,
    }),
    { total_rooms: 0, revenue: 0, stly_revenue: 0 },
  );

  const totalOcc = totals.total_rooms / (data.available_rooms_per_night * rows.length) || 0;
  const totalAdr = totals.total_rooms ? Math.round(totals.revenue / totals.total_rooms) : 0;
  const totalVsStlyPct = totals.stly_revenue
    ? Math.round(((totals.revenue - totals.stly_revenue) / totals.stly_revenue) * 1000) / 10
    : null;

  return (
    <DataTable title={`Next ${rows.length} Days \u2014 Daily OTB`}>
      <TableHeader>
        <Th align="left">Date</Th>
        <Th align="left">Day</Th>
        <Th>OTB Rooms</Th>
        <Th>Occ %</Th>
        <Th>ADR</Th>
        <Th>Revenue</Th>
        <Th>STLY OTB</Th>
        <Th>vs STLY</Th>
      </TableHeader>
      <tbody className="divide-y divide-surface-100">
        {rows.map((row) => {
          const d = new Date(row.date + "T00:00:00");
          const dateLabel = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
          const isWeekend = WEEKEND_DAYS.has(row.day_of_week);

          return (
            <tr
              key={row.date}
              className={cn("hover:bg-surface-50", isWeekend && "bg-blue-50/30")}
            >
              <td className="py-2.5 px-4">{dateLabel}</td>
              <td className="py-2.5 px-4 text-surface-500">{row.day_of_week}</td>
              <td className={cn("py-2.5 px-4 text-right tabular-nums", isWeekend && "font-medium")}>
                {row.total_rooms.toLocaleString()}
              </td>
              <td className={cn("py-2.5 px-4 text-right tabular-nums", isWeekend && "font-medium")}>
                {formatPercent(row.occupancy)}
              </td>
              <td className="py-2.5 px-4 text-right tabular-nums">
                {formatCurrency(row.adr)}
              </td>
              <td className="py-2.5 px-4 text-right tabular-nums font-medium">
                {formatCurrency(row.revenue)}
              </td>
              <td className="py-2.5 px-4 text-right tabular-nums text-surface-500">
                {formatCurrency(row.stly_revenue)}
              </td>
              <td className="py-2.5 px-4 text-right">
                {row.vs_stly_pct !== null ? (
                  <VarianceBadge
                    value={row.vs_stly_pct}
                    label={`${row.vs_stly_pct > 0 ? "+" : ""}${row.vs_stly_pct.toFixed(1)}%`}
                    favorable={row.vs_stly_pct > 0}
                  />
                ) : (
                  <span className="text-xs text-surface-400">&mdash;</span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
      <tfoot>
        <tr className="bg-surface-50 border-t border-surface-200 font-semibold">
          <td className="py-2.5 px-4" colSpan={2}>
            {rows.length}-Day Total
          </td>
          <td className="py-2.5 px-4 text-right tabular-nums">
            {totals.total_rooms.toLocaleString()}
          </td>
          <td className="py-2.5 px-4 text-right tabular-nums">{formatPercent(totalOcc)}</td>
          <td className="py-2.5 px-4 text-right tabular-nums">{formatCurrency(totalAdr)}</td>
          <td className="py-2.5 px-4 text-right tabular-nums">{formatCurrency(totals.revenue)}</td>
          <td className="py-2.5 px-4 text-right tabular-nums text-surface-600">
            {formatCurrency(totals.stly_revenue)}
          </td>
          <td className="py-2.5 px-4 text-right">
            {totalVsStlyPct !== null ? (
              <VarianceBadge
                value={totalVsStlyPct}
                label={`${totalVsStlyPct > 0 ? "+" : ""}${totalVsStlyPct.toFixed(1)}%`}
                favorable={totalVsStlyPct > 0}
              />
            ) : (
              <span className="text-xs text-surface-400">&mdash;</span>
            )}
          </td>
        </tr>
      </tfoot>
    </DataTable>
  );
}
