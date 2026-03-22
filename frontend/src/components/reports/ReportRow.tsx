"use client";

import { useEffect } from "react";
import { ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  formatCurrency,
  formatVarianceCurrency,
  formatVariancePercent,
  getVarianceColor,
} from "@/lib/formatters";
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
  hasBudget: boolean;
  hasStly: boolean;
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
  hasBudget,
  hasStly,
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
  const namePaddingLeft = 12 + depth * 24;

  // Three-tier hierarchy
  const isTier1 = depth === 0 && line_item.is_summary;
  const isTier2 = depth > 0 && line_item.is_summary;

  // Total columns for loading indicator colspan
  const totalCols =
    2 +
    (hasBudget ? 1 : 0) +
    (showForecast ? 1 : 0) +
    (hasStly ? 1 : 0) +
    (hasBudget ? 2 : 0) +
    (showForecast ? 2 : 0) +
    (hasStly ? 2 : 0);

  // First variance group gets border-l-2
  const firstVarianceGroup = hasBudget
    ? "budget"
    : showForecast
      ? "forecast"
      : hasStly
        ? "stly"
        : null;

  return (
    <>
      <tr
        className={cn(
          "transition-colors",
          canExpand && "cursor-pointer hover:bg-gray-50",
          isTier1 && "font-medium bg-gray-100 border-t-2 border-gray-200",
          isTier2 && "font-medium",
          !isTier1 && !isTier2 && "font-normal text-gray-700"
        )}
        onClick={() => canExpand && onToggleRow(line_item.id)}
      >
        {/* Name */}
        <td
          className={cn(
            "px-3 py-2 sticky left-0 z-10",
            isTier1 ? "bg-gray-100" : "bg-white"
          )}
          style={{ paddingLeft: `${namePaddingLeft}px`, minWidth: 200 }}
        >
          <div className="flex items-center gap-2">
            {canExpand &&
              (isExpanded ? (
                <ChevronDown className="h-4 w-4 shrink-0 text-gray-400" />
              ) : (
                <ChevronRight className="h-4 w-4 shrink-0 text-gray-400" />
              ))}
            <span className="text-sm">{line_item.name}</span>
          </div>
        </td>

        {/* Actual */}
        <td className="px-3 py-2 text-right tabular-nums whitespace-nowrap text-sm">
          {formatCurrency(row.actual)}
        </td>

        {/* Data zone: comparison values */}
        {hasBudget && (
          <td className="px-3 py-2 text-right tabular-nums whitespace-nowrap text-sm">
            {formatCurrency(row.budget)}
          </td>
        )}
        {showForecast && (
          <td className="px-3 py-2 text-right tabular-nums whitespace-nowrap text-sm">
            {row.forecast != null ? formatCurrency(row.forecast) : "-"}
          </td>
        )}
        {hasStly && (
          <td className="px-3 py-2 text-right tabular-nums whitespace-nowrap text-sm">
            {formatCurrency(row.prior_year_actual)}
          </td>
        )}

        {/* Variance zone: budget var $ and % */}
        {hasBudget && (
          <>
            <td
              className={cn(
                "px-3 py-2 text-right tabular-nums whitespace-nowrap text-sm",
                firstVarianceGroup === "budget" && "border-l-2 border-gray-200",
                getVarianceColor(row.variance_dollar, dataType)
              )}
            >
              {formatVarianceCurrency(row.variance_dollar)}
            </td>
            <td
              className={cn(
                "px-3 py-2 text-right tabular-nums whitespace-nowrap text-sm",
                getVarianceColor(row.variance_dollar, dataType)
              )}
            >
              {formatVariancePercent(row.variance_percent)}
            </td>
          </>
        )}

        {/* Variance zone: forecast var $ and % */}
        {showForecast && (
          <>
            <td
              className={cn(
                "px-3 py-2 text-right tabular-nums whitespace-nowrap text-sm",
                firstVarianceGroup === "forecast" && "border-l-2 border-gray-200",
                row.forecast_variance_dollar != null
                  ? getVarianceColor(row.forecast_variance_dollar, dataType)
                  : "text-gray-400"
              )}
            >
              {row.forecast_variance_dollar != null
                ? formatVarianceCurrency(row.forecast_variance_dollar)
                : "-"}
            </td>
            <td
              className={cn(
                "px-3 py-2 text-right tabular-nums whitespace-nowrap text-sm",
                row.forecast_variance_dollar != null
                  ? getVarianceColor(row.forecast_variance_dollar, dataType)
                  : "text-gray-400"
              )}
            >
              {row.forecast_variance_percent != null
                ? formatVariancePercent(row.forecast_variance_percent)
                : "-"}
            </td>
          </>
        )}

        {/* Variance zone: STLY var $ and % */}
        {hasStly && (
          <>
            <td
              className={cn(
                "px-3 py-2 text-right tabular-nums whitespace-nowrap text-sm",
                firstVarianceGroup === "stly" && "border-l-2 border-gray-200",
                getVarianceColor(row.py_variance_dollar, dataType)
              )}
            >
              {formatVarianceCurrency(row.py_variance_dollar)}
            </td>
            <td
              className={cn(
                "px-3 py-2 text-right tabular-nums whitespace-nowrap text-sm",
                getVarianceColor(row.py_variance_dollar, dataType)
              )}
            >
              {formatVariancePercent(row.py_variance_percent)}
            </td>
          </>
        )}
      </tr>

      {/* Loading indicator */}
      {isExpanded && childrenLoading && !cachedChildren && (
        <tr>
          <td colSpan={totalCols} className="py-2 text-center">
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
            hasBudget={hasBudget}
            hasStly={hasStly}
            propertyId={propertyId}
            period={period}
          />
        ))}
    </>
  );
}
