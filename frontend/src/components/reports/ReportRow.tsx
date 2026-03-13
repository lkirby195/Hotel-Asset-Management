"use client";

import { useEffect } from "react";
import { ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatCurrency, formatVarianceCurrency, formatVariancePercent, getVarianceColor } from "@/lib/formatters";
import { useChildRows } from "@/hooks/useReportData";
import type { ReportRow as ReportRowType } from "@/types/reports";

interface ReportRowProps {
  row: ReportRowType;
  depth: number;
  isExpanded: boolean;
  expandedRows: Set<string>;
  childRowsMap: Map<string, ReportRowType[]>;
  onToggleRow: (id: string) => void;
  onChildrenLoaded: (parentId: string, children: ReportRowType[]) => void;
  showForecast: boolean;
  propertyId: string;
  period: string;
}

export function ReportRow({
  row,
  depth,
  isExpanded,
  expandedRows,
  childRowsMap,
  onToggleRow,
  onChildrenLoaded,
  showForecast,
  propertyId,
  period,
}: ReportRowProps) {
  const { line_item } = row;
  const canExpand = line_item.is_summary && line_item.has_children;

  const { data: children, isLoading: childrenLoading } = useChildRows(
    propertyId,
    period,
    isExpanded ? line_item.id : null
  );

  useEffect(() => {
    if (children && children.length > 0) {
      onChildrenLoaded(line_item.id, children);
    }
  }, [children, line_item.id, onChildrenLoaded]);

  const cachedChildren = childRowsMap.get(line_item.id);
  const dataType = line_item.data_type;
  const isChild = depth > 0;
  const namePaddingLeft = 12 + depth * 24;

  return (
    <>
      <tr
        className={cn(
          "transition-colors",
          canExpand && "cursor-pointer hover:bg-gray-50",
          line_item.is_summary && "font-medium",
          depth === 0 && line_item.is_summary && "bg-gray-50/50"
        )}
        onClick={() => canExpand && onToggleRow(line_item.id)}
      >
        {/* Name */}
        <td className="px-3 py-2" style={{ paddingLeft: `${namePaddingLeft}px` }}>
          <div className="flex items-center gap-2">
            {canExpand &&
              (isExpanded ? (
                <ChevronDown className="h-4 w-4 shrink-0 text-gray-400" />
              ) : (
                <ChevronRight className="h-4 w-4 shrink-0 text-gray-400" />
              ))}
            <span
              className={cn(
                isChild && !line_item.is_summary && "text-xs text-gray-500",
                !isChild && "text-sm text-gray-900"
              )}
            >
              {line_item.name}
            </span>
          </div>
        </td>

        {/* Actual */}
        <td className={cn("px-3 py-2 text-right tabular-nums", isChild && "text-xs")}>
          {formatCurrency(row.actual)}
        </td>

        {/* Budget */}
        <td className={cn("px-3 py-2 text-right tabular-nums", isChild && "text-xs")}>
          {formatCurrency(row.budget)}
        </td>

        {/* Variance $ */}
        <td
          className={cn(
            "px-3 py-2 text-right tabular-nums",
            isChild && "text-xs",
            getVarianceColor(row.variance_dollar, dataType)
          )}
        >
          {formatVarianceCurrency(row.variance_dollar)}
        </td>

        {/* Variance % */}
        <td
          className={cn(
            "px-3 py-2 text-right tabular-nums",
            isChild && "text-xs",
            getVarianceColor(row.variance_dollar, dataType)
          )}
        >
          {formatVariancePercent(row.variance_percent)}
        </td>

        {/* PY Actual */}
        <td className={cn("px-3 py-2 text-right tabular-nums", isChild && "text-xs")}>
          {formatCurrency(row.prior_year_actual)}
        </td>

        {/* PY Var $ */}
        <td
          className={cn(
            "px-3 py-2 text-right tabular-nums",
            isChild && "text-xs",
            getVarianceColor(row.py_variance_dollar, dataType)
          )}
        >
          {formatVarianceCurrency(row.py_variance_dollar)}
        </td>

        {/* Forecast columns (month-end only) */}
        {showForecast && (
          <>
            <td className={cn("px-3 py-2 text-right tabular-nums", isChild && "text-xs")}>
              {row.forecast != null ? formatCurrency(row.forecast) : "\u2014"}
            </td>
            <td
              className={cn(
                "px-3 py-2 text-right tabular-nums",
                isChild && "text-xs",
                row.forecast_variance_dollar != null
                  ? getVarianceColor(row.forecast_variance_dollar, dataType)
                  : "text-gray-400"
              )}
            >
              {row.forecast_variance_dollar != null
                ? formatVarianceCurrency(row.forecast_variance_dollar)
                : "\u2014"}
            </td>
          </>
        )}
      </tr>

      {/* Loading indicator */}
      {isExpanded && childrenLoading && !cachedChildren && (
        <tr>
          <td colSpan={showForecast ? 9 : 7} className="py-2 text-center">
            <Loader2 className="mx-auto h-4 w-4 animate-spin text-gray-400" />
          </td>
        </tr>
      )}

      {/* Child rows */}
      {isExpanded &&
        (cachedChildren ?? children ?? []).map((childRow) => (
          <ReportRow
            key={childRow.line_item.id}
            row={childRow}
            depth={depth + 1}
            isExpanded={expandedRows.has(childRow.line_item.id)}
            expandedRows={expandedRows}
            childRowsMap={childRowsMap}
            onToggleRow={onToggleRow}
            onChildrenLoaded={onChildrenLoaded}
            showForecast={showForecast}
            propertyId={propertyId}
            period={period}
          />
        ))}
    </>
  );
}
