"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import type { ReportData, ReportRow } from "@/types/reports";
import type { ApiResponse } from "@/types/api";

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
      const { data } = await api.get<ApiResponse<ReportData>>(
        `/reports/inter-month/${propertyId}?${params}`
      );
      return data.data;
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
      const { data } = await api.get<ApiResponse<ReportRow[]>>(
        `/reports/inter-month/${propertyId}/children/${parentLineItemId}?period=${period}`
      );
      return data.data;
    },
    enabled: !!propertyId && !!parentLineItemId,
  });
}
