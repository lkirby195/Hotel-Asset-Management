"use client";

import { cn } from "@/lib/utils";
import type { DailyReportSection, DualPanelRow } from "@/types/daily-report";

/* ── Formatters ─────────────────────────────────── */

function fmtValue(val: number | null, unit: string): string {
  if (val == null) return "—";
  switch (unit) {
    case "currency": {
      const abs = Math.abs(val);
      if (abs >= 1_000_000) return `${val < 0 ? "-" : ""}$${(abs / 1_000_000).toFixed(2)}M`;
      if (abs >= 1_000) return `${val < 0 ? "-" : ""}$${Math.round(abs).toLocaleString()}`;
      return `${val < 0 ? "-" : ""}$${abs.toFixed(0)}`;
    }
    case "percent":
      return `${val.toFixed(1)}%`;
    case "pts":
      return `${val.toFixed(1)}pt`;
    case "number":
      return Math.round(val).toLocaleString();
    default:
      return String(val);
  }
}

function fmtVariance(val: number | null, unit: string): string {
  if (val == null) return "—";
  const sign = val > 0 ? "+" : "";
  switch (unit) {
    case "currency": {
      const abs = Math.abs(val);
      if (abs >= 1_000_000) return `${sign}$${(val / 1_000_000).toFixed(2)}M`;
      if (abs >= 1_000) return `${sign}$${Math.round(val).toLocaleString()}`;
      return `${sign}$${val.toFixed(0)}`;
    }
    case "percent":
      return `${sign}${val.toFixed(1)}%`;
    case "pts":
      return `${sign}${val.toFixed(1)}pt`;
    case "number":
      return `${sign}${Math.round(val).toLocaleString()}`;
    default:
      return `${sign}${val}`;
  }
}

function varianceCls(val: number | null): string {
  if (val == null || val === 0) return "text-surface-500 bg-surface-100";
  return val > 0
    ? "text-positive-700 bg-positive-50"
    : "text-negative-700 bg-negative-50";
}

/* ── Row renderer ───────────────────────────────── */

function DailyRow({ row }: { row: DualPanelRow }) {
  if (row.is_header) {
    return (
      <tr className="bg-surface-50 font-semibold">
        <td className="py-2 px-3" colSpan={6}>
          {row.line_name}
        </td>
      </tr>
    );
  }

  const indent = row.indent > 0 ? row.indent * 16 + 12 : 12;

  return (
    <tr
      className={cn(
        row.is_total
          ? "bg-surface-100 font-bold border-t-2 border-surface-300"
          : "hover:bg-surface-50",
      )}
    >
      <td className="py-2 px-3" style={{ paddingLeft: indent }}>
        {row.line_name}
      </td>
      <td className="py-2 px-3 text-right font-semibold">
        {fmtValue(row.daily_actual, row.unit)}
      </td>
      <td className="py-2 px-3 text-right text-surface-600">
        {fmtValue(row.daily_forecast, row.unit)}
      </td>
      <td className="py-2 px-3 text-right text-surface-600">
        {fmtValue(row.daily_stly, row.unit)}
      </td>
      <td className="py-2 px-3 text-right">
        <span
          className={cn(
            "inline-flex px-1 py-0.5 rounded text-[10px] font-medium",
            varianceCls(row.daily_vs_forecast),
          )}
        >
          {fmtVariance(row.daily_vs_forecast, row.unit)}
        </span>
      </td>
      <td className="py-2 px-3 text-right">
        <span
          className={cn(
            "inline-flex px-1 py-0.5 rounded text-[10px] font-medium",
            varianceCls(row.daily_vs_stly),
          )}
        >
          {fmtVariance(row.daily_vs_stly, row.unit)}
        </span>
      </td>
    </tr>
  );
}

function MTDRow({ row }: { row: DualPanelRow }) {
  if (row.is_header) {
    return (
      <tr className="bg-surface-50 font-semibold">
        <td className="py-2 px-3" colSpan={7}>
          {row.line_name}
        </td>
      </tr>
    );
  }

  const indent = row.indent > 0 ? row.indent * 16 + 12 : 12;

  return (
    <tr
      className={cn(
        row.is_total
          ? "bg-surface-100 font-bold border-t-2 border-surface-300"
          : "hover:bg-surface-50",
      )}
    >
      <td className="py-2 px-3" style={{ paddingLeft: indent }}>
        {row.line_name}
      </td>
      <td className="py-2 px-3 text-right font-semibold">
        {fmtValue(row.mtd_actual, row.unit)}
      </td>
      <td className="py-2 px-3 text-right text-surface-600">
        {fmtValue(row.mtd_budget, row.unit)}
      </td>
      <td className="py-2 px-3 text-right text-surface-600">
        {fmtValue(row.mtd_stly, row.unit)}
      </td>
      <td className="py-2 px-3 text-right text-surface-600">
        {fmtValue(row.mtd_fcst_lock, row.unit)}
      </td>
      <td className="py-2 px-3 text-right">
        <span
          className={cn(
            "inline-flex px-1 py-0.5 rounded text-[10px] font-medium",
            varianceCls(row.mtd_vs_budget),
          )}
        >
          {fmtVariance(row.mtd_vs_budget, row.unit)}
        </span>
      </td>
      <td className="py-2 px-3 text-right">
        <span
          className={cn(
            "inline-flex px-1 py-0.5 rounded text-[10px] font-medium",
            varianceCls(row.mtd_vs_stly),
          )}
        >
          {fmtVariance(row.mtd_vs_stly, row.unit)}
        </span>
      </td>
    </tr>
  );
}

/* ── Main component ─────────────────────────────── */

interface DualPanelTableProps {
  sections: DailyReportSection[];
  reportDate: string;
  mtdRange: string;
  mtdProgress: string;
}

export function DualPanelTable({
  sections,
  reportDate,
  mtdRange,
  mtdProgress,
}: DualPanelTableProps) {
  const allRows = sections.flatMap((s) => s.rows);

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
      {/* DAILY PANEL */}
      <div className="bg-white rounded-xl border border-surface-200 overflow-hidden">
        <div className="bg-surface-900 text-white px-4 py-3 flex items-center justify-between">
          <span className="text-sm font-semibold">Daily — {reportDate}</span>
          <span className="text-xs text-surface-300">
            {new Date(reportDate).toLocaleDateString("en-US", { weekday: "long" })}
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-surface-50 border-b border-surface-200">
                <th className="text-left py-2 px-3 font-semibold text-surface-500 w-[30%]" />
                <th className="text-right py-2 px-3 font-semibold text-surface-500">Actual</th>
                <th className="text-right py-2 px-3 font-semibold text-surface-500">Forecast</th>
                <th className="text-right py-2 px-3 font-semibold text-surface-500">STLY</th>
                <th className="text-right py-2 px-3 font-semibold text-surface-500">vs Fcst</th>
                <th className="text-right py-2 px-3 font-semibold text-surface-500">vs STLY</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-100">
              {allRows.map((row, i) => (
                <DailyRow key={`${row.line_name}-${i}`} row={row} />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* MTD PANEL */}
      <div className="bg-white rounded-xl border border-surface-200 overflow-hidden border-l-4 border-l-brand-500">
        <div className="bg-brand-700 text-white px-4 py-3 flex items-center justify-between">
          <span className="text-sm font-semibold">MTD — {mtdRange}</span>
          <span className="text-xs text-brand-200">{mtdProgress}</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-surface-50 border-b border-surface-200">
                <th className="text-left py-2 px-3 font-semibold text-surface-500 w-[26%]" />
                <th className="text-right py-2 px-3 font-semibold text-surface-500">Actual</th>
                <th className="text-right py-2 px-3 font-semibold text-surface-500">Budget</th>
                <th className="text-right py-2 px-3 font-semibold text-surface-500">STLY</th>
                <th className="text-right py-2 px-3 font-semibold text-surface-500">Fcst Lock</th>
                <th className="text-right py-2 px-3 font-semibold text-surface-500">vs Bgt</th>
                <th className="text-right py-2 px-3 font-semibold text-surface-500">vs STLY</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-100">
              {allRows.map((row, i) => (
                <MTDRow key={`${row.line_name}-${i}`} row={row} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
