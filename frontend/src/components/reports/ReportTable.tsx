"use client";

import { ReportRow } from "./ReportRow";
import type { ReportRow as ReportRowType } from "@/types/reports";
import type { ComparisonType } from "@/types/reports";

interface ReportTableProps {
  rows: ReportRowType[];
  expandedRows: Set<string>;
  childRowsMap: Map<string, ReportRowType[]>;
  onToggleRow: (id: string) => void;
  onChildrenLoaded: (parentId: string, children: ReportRowType[]) => void;
  showForecast: boolean;
  propertyId: string;
  period: string;
  activeComparisons?: Set<ComparisonType>;
}

export function ReportTable({
  rows,
  expandedRows,
  childRowsMap,
  onToggleRow,
  onChildrenLoaded,
  showForecast,
  propertyId,
  period,
  activeComparisons,
}: ReportTableProps) {
  const comparisons = activeComparisons ?? new Set<ComparisonType>(["budget"]);
  const hasBudget = comparisons.has("budget");
  const hasForecast = comparisons.has("forecast_lock") || showForecast;
  const hasStly = comparisons.has("stly");

  // Count variance columns for colspan calculations
  const varianceColCount =
    (hasBudget ? 2 : 0) + (hasForecast ? 2 : 0) + (hasStly ? 2 : 0);

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
      <table className="w-full">
        <thead>
          <tr className="border-b-2 border-gray-200 bg-gray-100 text-xs font-medium uppercase tracking-wide text-gray-500">
            {/* Data zone */}
            <th
              className="px-3 py-2.5 text-left sticky left-0 bg-gray-100 z-10"
              style={{ minWidth: 200 }}
            >
              Line item
            </th>
            <th
              className="px-3 py-2.5 text-right whitespace-nowrap"
              style={{ minWidth: 100 }}
            >
              Actual
            </th>
            {hasBudget && (
              <th
                className="px-3 py-2.5 text-right whitespace-nowrap"
                style={{ minWidth: 100 }}
              >
                Budget
              </th>
            )}
            {hasForecast && (
              <th
                className="px-3 py-2.5 text-right whitespace-nowrap"
                style={{ minWidth: 100 }}
              >
                Fcst Lock
              </th>
            )}
            {hasStly && (
              <th
                className="px-3 py-2.5 text-right whitespace-nowrap"
                style={{ minWidth: 100 }}
              >
                STLY
              </th>
            )}

            {/* Variance zone - separated by border */}
            {hasBudget && (
              <>
                <th
                  className="px-3 py-2.5 text-right whitespace-nowrap border-l-2 border-gray-200"
                  style={{ minWidth: 100 }}
                >
                  Bgt Var $
                </th>
                <th
                  className="px-3 py-2.5 text-right whitespace-nowrap"
                  style={{ minWidth: 70 }}
                >
                  Bgt Var %
                </th>
              </>
            )}
            {hasForecast && (
              <>
                <th
                  className={`px-3 py-2.5 text-right whitespace-nowrap${!hasBudget ? " border-l-2 border-gray-200" : ""}`}
                  style={{ minWidth: 100 }}
                >
                  Fcst Var $
                </th>
                <th
                  className="px-3 py-2.5 text-right whitespace-nowrap"
                  style={{ minWidth: 70 }}
                >
                  Fcst Var %
                </th>
              </>
            )}
            {hasStly && (
              <>
                <th
                  className={`px-3 py-2.5 text-right whitespace-nowrap${!hasBudget && !hasForecast ? " border-l-2 border-gray-200" : ""}`}
                  style={{ minWidth: 100 }}
                >
                  PY Var $
                </th>
                <th
                  className="px-3 py-2.5 text-right whitespace-nowrap"
                  style={{ minWidth: 70 }}
                >
                  PY Var %
                </th>
              </>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.map((row) => (
            <ReportRow
              key={row.line_item.id}
              row={row}
              depth={0}
              isExpanded={expandedRows.has(row.line_item.id)}
              expandedRows={expandedRows}
              childRowsMap={childRowsMap}
              onToggleRow={onToggleRow}
              onChildrenLoaded={onChildrenLoaded}
              showForecast={hasForecast}
              hasBudget={hasBudget}
              hasStly={hasStly}
              propertyId={propertyId}
              period={period}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
