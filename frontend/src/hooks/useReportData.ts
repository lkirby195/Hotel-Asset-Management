"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import type { ReportData, ReportRow } from "@/types/reports";
import type { ApiResponse } from "@/types/api";

// The backend returns a flat line-item format; transform to the nested ReportRow shape
interface ApiLineItem {
  id: string;
  code: string;
  name: string;
  parent_id: string | null;
  is_summary: boolean;
  data_type: "revenue" | "expense";
  sort_order: number;
  depth: number;
  actual: number;
  budget: number;
  variance_dollars: number;
  variance_pct: number | null;
  prior_year_actual: number | null;
  py_variance_dollars: number | null;
  py_variance_pct: number | null;
}

interface ApiReportData {
  property_id: string;
  property_name: string;
  period: string;
  start_date: string;
  end_date: string;
  lines: ApiLineItem[];
}

function transformLine(line: ApiLineItem): ReportRow {
  return {
    line_item: {
      id: line.id,
      code: line.code,
      name: line.name,
      parent_id: line.parent_id,
      department_type: null,
      sort_order: line.sort_order,
      is_summary: line.is_summary,
      data_type: line.data_type,
      has_children: line.is_summary,
    },
    actual: line.actual,
    budget: line.budget,
    variance_dollar: line.variance_dollars,
    variance_percent: line.variance_pct ?? 0,
    prior_year_actual: line.prior_year_actual ?? 0,
    py_variance_dollar: line.py_variance_dollars ?? 0,
    py_variance_percent: line.py_variance_pct ?? 0,
  };
}

function transformReport(api: ApiReportData): ReportData {
  return {
    property_id: api.property_id,
    property_name: api.property_name,
    period: { type: api.period as ReportData["period"]["type"] },
    as_of_date: api.end_date,
    rows: api.lines.map(transformLine),
    last_synced: "",
  };
}

export function useReportData(
  propertyId: string | null,
  period: string,
  startDate?: string,
  endDate?: string
) {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);

  return useQuery({
    queryKey: ["report", "inter-month", propertyId, period, startDate, endDate],
    queryFn: async () => {
      const params = new URLSearchParams({ period });
      if (startDate) params.set("start", startDate);
      if (endDate) params.set("end", endDate);
      const { data } = await api.get<ApiResponse<ApiReportData>>(
        `/reports/inter-month/${propertyId}?${params}`
      );
      return transformReport(data.data);
    },
    enabled: !!propertyId,
    placeholderData: (prev) => prev,
  });
}

export function useChildRows(
  propertyId: string,
  period: string,
  parentLineItemId: string | null
) {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);

  return useQuery({
    queryKey: ["report", "children", propertyId, period, parentLineItemId],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<ApiLineItem[]>>(
        `/reports/inter-month/${propertyId}/children/${parentLineItemId}?period=${period}`
      );
      return data.data.map(transformLine);
    },
    enabled: !!propertyId && !!parentLineItemId,
  });
}
