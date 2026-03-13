"use client";

import { ReportRow } from "./ReportRow";
import type { ReportRow as ReportRowType } from "@/types/reports";

interface ReportTableProps {
  rows: ReportRowType[];
  expandedRows: Set<string>;
  childRowsMap: Map<string, ReportRowType[]>;
  onToggleRow: (id: string) => void;
  onChildrenLoaded: (parentId: string, children: ReportRowType[]) => void;
  showForecast: boolean;
  propertyId: string;
  period: string;
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
}: ReportTableProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table className="w-full">
        <thead>
          <tr className="border-b bg-surface text-xs font-medium uppercase tracking-wide text-gray-500">
            <th className="px-3 py-3 text-left" style={{ width: "28%" }}>
              Line item
            </th>
            <th className="px-3 py-3 text-right" style={{ width: "12%" }}>
              Actual
            </th>
            <th className="px-3 py-3 text-right" style={{ width: "12%" }}>
              Budget
            </th>
            <th className="px-3 py-3 text-right" style={{ width: "10%" }}>
              Var $
            </th>
            <th className="px-3 py-3 text-right" style={{ width: "8%" }}>
              Var %
            </th>
            <th className="px-3 py-3 text-right" style={{ width: "12%" }}>
              PY actual
            </th>
            <th className="px-3 py-3 text-right" style={{ width: "10%" }}>
              PY var $
            </th>
            {showForecast && (
              <>
                <th className="px-3 py-3 text-right" style={{ width: "10%" }}>
                  Forecast
                </th>
                <th className="px-3 py-3 text-right" style={{ width: "10%" }}>
                  Fcst var $
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
              showForecast={showForecast}
              propertyId={propertyId}
              period={period}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
