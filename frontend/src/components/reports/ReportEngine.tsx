"use client";

import { useState, useCallback } from "react";
import { ReportTable } from "./ReportTable";
import { TableSkeleton } from "@/components/shared/LoadingSkeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import { useChildRows } from "@/hooks/useReportData";
import type { ReportData, ReportRow } from "@/types/reports";

interface ReportEngineProps {
  data: ReportData | null;
  isLoading: boolean;
  propertyId: string;
  period: string;
  customStart?: string;
  customEnd?: string;
  showForecast?: boolean;
}

export function ReportEngine({
  data,
  isLoading,
  propertyId,
  period,
  showForecast = false,
}: ReportEngineProps) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [childRowsMap, setChildRowsMap] = useState<Map<string, ReportRow[]>>(
    new Map()
  );

  const onToggleRow = useCallback((lineItemId: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(lineItemId)) {
        next.delete(lineItemId);
      } else {
        next.add(lineItemId);
      }
      return next;
    });
  }, []);

  const onChildrenLoaded = useCallback(
    (parentId: string, children: ReportRow[]) => {
      setChildRowsMap((prev) => new Map(prev).set(parentId, children));
    },
    []
  );

  if (isLoading) return <TableSkeleton />;

  if (!data || data.rows.length === 0) {
    return <EmptyState message="No data available for the selected period." />;
  }

  return (
    <ReportTable
      rows={data.rows}
      expandedRows={expandedRows}
      childRowsMap={childRowsMap}
      onToggleRow={onToggleRow}
      onChildrenLoaded={onChildrenLoaded}
      showForecast={showForecast}
      propertyId={propertyId}
      period={period}
    />
  );
}
