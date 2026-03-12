"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { AccordionRow } from "./accordion-row";
import type { ReportLineItem } from "@/lib/types";

interface ReportTableProps {
  lines: ReportLineItem[];
  period: string;
  isLoading: boolean;
}

function ReportTableSkeleton() {
  return (
    <div className="space-y-2 rounded-lg border bg-white p-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}

export function ReportTable({ lines, period, isLoading }: ReportTableProps) {
  if (isLoading) return <ReportTableSkeleton />;

  if (lines.length === 0) {
    return (
      <div className="rounded-lg border bg-white p-8 text-center text-gray-500">
        No data available for the selected period.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border bg-white shadow-sm">
      <table className="w-full">
        <thead>
          <tr className="border-b bg-gray-50 text-xs font-medium uppercase tracking-wider text-gray-500">
            <th className="px-3 py-3 text-left">Line Item</th>
            <th className="px-3 py-3 text-right">Actual</th>
            <th className="px-3 py-3 text-right">Budget</th>
            <th className="px-3 py-3 text-right">Variance</th>
            <th className="px-3 py-3 text-right">Prior Year</th>
            <th className="px-3 py-3 text-right">PY Variance</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {lines.map((line) => (
            <AccordionRow
              key={line.id}
              line={line}
              depth={0}
              period={period}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
