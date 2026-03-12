"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLineItemChildren } from "@/hooks/use-inter-month-report";
import { CurrencyCell } from "./currency-cell";
import { VarianceCell } from "./variance-cell";
import type { ReportLineItem } from "@/lib/types";

interface AccordionRowProps {
  line: ReportLineItem;
  depth: number;
  period: string;
}

export function AccordionRow({ line, depth, period }: AccordionRowProps) {
  const [expanded, setExpanded] = useState(false);
  const { data: children, isLoading } = useLineItemChildren(
    expanded ? line.id : null,
    period
  );

  return (
    <>
      <tr
        className={cn(
          "transition-colors hover:bg-gray-50",
          line.is_summary && "cursor-pointer font-semibold",
          depth === 0 && line.is_summary && "bg-gray-50/50"
        )}
        onClick={() => line.is_summary && setExpanded(!expanded)}
      >
        <td
          className="px-3 py-2"
          style={{ paddingLeft: `${12 + depth * 24}px` }}
        >
          <div className="flex items-center gap-2">
            {line.is_summary &&
              (expanded ? (
                <ChevronDown className="h-4 w-4 shrink-0" />
              ) : (
                <ChevronRight className="h-4 w-4 shrink-0" />
              ))}
            <span className={cn(depth > 0 && !line.is_summary && "text-sm")}>
              {line.name}
            </span>
          </div>
        </td>
        <CurrencyCell value={line.actual} />
        <CurrencyCell value={line.budget} />
        <VarianceCell
          value={line.variance_dollars}
          percentage={line.variance_pct}
          dataType={line.data_type}
        />
        <CurrencyCell value={line.prior_year_actual} />
        {line.py_variance_dollars !== null ? (
          <VarianceCell
            value={line.py_variance_dollars}
            percentage={line.py_variance_pct}
            dataType={line.data_type}
          />
        ) : (
          <td className="px-3 py-2 text-right text-gray-400">—</td>
        )}
      </tr>

      {expanded && isLoading && (
        <tr>
          <td colSpan={6} className="py-2 text-center">
            <Loader2 className="mx-auto h-4 w-4 animate-spin text-gray-400" />
          </td>
        </tr>
      )}

      {expanded &&
        children?.map((child) => (
          <AccordionRow
            key={child.id}
            line={child}
            depth={depth + 1}
            period={period}
          />
        ))}
    </>
  );
}
