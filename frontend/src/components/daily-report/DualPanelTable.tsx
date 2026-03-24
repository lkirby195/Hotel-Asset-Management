"use client";

import React from "react";
import { cn } from "@/lib/utils";
import {
  formatCurrency,
  formatVarianceCurrency,
  formatPercent,
  formatVariancePercent,
  formatInteger,
  formatVarianceInteger,
  formatDecimal,
  formatVarianceDecimal,
} from "@/lib/formatters";
import type { DailyReportSection, DualPanelRow } from "@/types/daily-report";

interface DualPanelTableProps {
  sections: DailyReportSection[];
}

function formatValue(value: number | null, unit: string): string {
  if (value === null || value === undefined) return "—";
  switch (unit) {
    case "currency":
      return formatCurrency(value);
    case "percentage":
      return formatPercent(value);
    case "integer":
      return formatInteger(value);
    case "decimal":
      return formatDecimal(value);
    default:
      return String(value);
  }
}

function formatVariance(value: number | null, unit: string): string {
  if (value === null || value === undefined) return "—";
  switch (unit) {
    case "currency":
      return formatVarianceCurrency(value);
    case "percentage":
      return formatVariancePercent(value);
    case "integer":
      return formatVarianceInteger(value);
    case "decimal":
      return formatVarianceDecimal(value);
    default:
      return String(value);
  }
}

function varianceColor(value: number | null, lineName: string): string {
  if (value === null || value === 0) return "text-gray-500";
  const isExpense =
    lineName.includes("Labor") ||
    lineName.includes("Wages") ||
    lineName.includes("Hours");
  const isFavorable = isExpense ? value < 0 : value > 0;
  return isFavorable ? "text-favorable" : "text-unfavorable";
}

function VarianceBadge({
  value,
  unit,
  lineName,
}: {
  value: number | null;
  unit: string;
  lineName: string;
}) {
  if (value === null || value === undefined) return <span className="text-gray-400">—</span>;
  const color = varianceColor(value, lineName);
  return (
    <span className={cn("text-xs font-medium whitespace-nowrap", color)}>
      {formatVariance(value, unit)}
    </span>
  );
}

function PendingCell({ value, unit, className: cls }: { value: number | null; unit: string; className?: string }) {
  if (value === null || value === undefined) {
    return (
      <td className={cn(cls)} title="Pending STR integration">
        <span className="text-gray-400">—</span>
      </td>
    );
  }
  return <td className={cn(cls)}>{formatValue(value, unit)}</td>;
}

function SectionHeaderRow({ name }: { name: string }) {
  return (
    <tr className="bg-gray-100 border-b border-gray-200">
      <td
        colSpan={12}
        className="px-3 py-2 text-xs font-bold uppercase tracking-wide text-gray-600"
      >
        {name}
      </td>
    </tr>
  );
}

function RowCells({ row, isPendingStr }: { row: DualPanelRow; isPendingStr?: boolean }) {
  const indent = row.indent * 12;

  // For STR rows with null values, use PendingCell to show tooltip
  const renderCell = (value: number | null, unit: string, cls: string) => {
    if (isPendingStr && (value === null || value === undefined)) {
      return <PendingCell value={value} unit={unit} className={cls} />;
    }
    return <td className={cls}>{formatValue(value, unit)}</td>;
  };

  const renderVarianceCell = (value: number | null, unit: string, lineName: string, cls: string) => {
    if (isPendingStr && (value === null || value === undefined)) {
      return <PendingCell value={value} unit={unit} className={cls} />;
    }
    return (
      <td className={cls}>
        <VarianceBadge value={value} unit={unit} lineName={lineName} />
      </td>
    );
  };

  return (
    <tr
      className={cn(
        "border-b border-gray-100 last:border-b-0",
        row.is_header && "bg-gray-50",
        row.is_total && "font-semibold bg-gray-50/50 border-t border-gray-200"
      )}
    >
      {/* Line name */}
      <td
        className={cn(
          "px-3 py-1.5 whitespace-nowrap text-gray-900",
          row.is_header && "font-semibold text-xs uppercase tracking-wide text-gray-600",
          row.is_total && "font-semibold"
        )}
        style={{ paddingLeft: `${12 + indent}px` }}
      >
        {row.line_name}
      </td>

      {/* Daily panel */}
      {row.is_header ? (
        <>
          <td className="px-2 py-1.5" />
          <td className="px-2 py-1.5" />
          <td className="px-2 py-1.5" />
          <td className="px-2 py-1.5" />
          <td className="px-2 py-1.5" />
        </>
      ) : (
        <>
          {renderCell(row.daily_actual, row.unit, "px-2 py-1.5 text-right tabular-nums font-medium text-gray-900")}
          {renderCell(row.daily_forecast, row.unit, "px-2 py-1.5 text-right tabular-nums text-gray-500")}
          {renderCell(row.daily_stly, row.unit, "px-2 py-1.5 text-right tabular-nums text-gray-500")}
          {renderVarianceCell(row.daily_vs_forecast, row.unit, row.line_name, "px-2 py-1.5 text-right")}
          {renderVarianceCell(row.daily_vs_stly, row.unit, row.line_name, "px-2 py-1.5 text-right")}
        </>
      )}

      {/* MTD panel */}
      {row.is_header ? (
        <>
          <td className="px-2 py-1.5 border-l-2 border-blue-200" />
          <td className="px-2 py-1.5" />
          <td className="px-2 py-1.5" />
          <td className="px-2 py-1.5" />
          <td className="px-2 py-1.5" />
          <td className="px-2 py-1.5" />
        </>
      ) : (
        <>
          {renderCell(row.mtd_actual, row.unit, "px-2 py-1.5 text-right tabular-nums font-medium text-gray-900 border-l-2 border-blue-200")}
          {renderCell(row.mtd_budget, row.unit, "px-2 py-1.5 text-right tabular-nums text-gray-500")}
          {renderCell(row.mtd_stly, row.unit, "px-2 py-1.5 text-right tabular-nums text-gray-500")}
          {renderCell(row.mtd_fcst_lock, row.unit, "px-2 py-1.5 text-right tabular-nums text-gray-500")}
          {renderVarianceCell(row.mtd_vs_budget, row.unit, row.line_name, "px-2 py-1.5 text-right")}
          {renderVarianceCell(row.mtd_vs_stly, row.unit, row.line_name, "px-2 py-1.5 text-right")}
        </>
      )}
    </tr>
  );
}

export function DualPanelTable({ sections }: DualPanelTableProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            {/* Panel headers */}
            <tr>
              <th className="bg-gray-50" />
              <th
                colSpan={5}
                className="px-2 py-2 text-center text-xs font-semibold text-white bg-gray-700 uppercase tracking-wider"
              >
                Daily
              </th>
              <th
                colSpan={6}
                className="px-2 py-2 text-center text-xs font-semibold text-white bg-blue-700 uppercase tracking-wider border-l-2 border-blue-200"
              >
                MTD
              </th>
            </tr>
            {/* Column headers */}
            <tr className="border-b border-gray-200 bg-gray-50 text-[10px] font-medium text-gray-500 uppercase tracking-wide">
              <th className="px-3 py-2 text-left w-40">Line Item</th>
              <th className="px-2 py-2 text-right">Actual</th>
              <th className="px-2 py-2 text-right">Forecast</th>
              <th className="px-2 py-2 text-right">STLY</th>
              <th className="px-2 py-2 text-right">vs Fcst</th>
              <th className="px-2 py-2 text-right">vs STLY</th>
              <th className="px-2 py-2 text-right border-l-2 border-blue-200">Actual</th>
              <th className="px-2 py-2 text-right">Budget</th>
              <th className="px-2 py-2 text-right">STLY</th>
              <th className="px-2 py-2 text-right">Fcst Lock</th>
              <th className="px-2 py-2 text-right">vs Budget</th>
              <th className="px-2 py-2 text-right">vs STLY</th>
            </tr>
          </thead>
          <tbody>
            {sections.map((section) => {
              const isPendingStr = section.section_name.toLowerCase().includes("str");
              return (
                <React.Fragment key={section.section_name}>
                  <SectionHeaderRow name={section.section_name} />
                  {section.rows.map((row, idx) => (
                    <RowCells
                      key={`${section.section_name}-${idx}`}
                      row={row}
                      isPendingStr={isPendingStr}
                    />
                  ))}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
