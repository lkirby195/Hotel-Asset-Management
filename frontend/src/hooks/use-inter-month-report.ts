"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useProperty } from "@/providers/property-provider";
import { createApiClient } from "@/lib/api-client";
import type { APIResponse, InterMonthReport, ReportLineItem } from "@/lib/types";

export function useInterMonthReport(
  period: string,
  startDate?: string,
  endDate?: string
) {
  const { selectedPropertyId } = useProperty();
  const { getToken } = useAuth();
  const api = createApiClient(getToken);

  return useQuery({
    queryKey: ["inter-month", selectedPropertyId, period, startDate, endDate],
    queryFn: async () => {
      const params = new URLSearchParams({ period });
      if (startDate) params.set("start", startDate);
      if (endDate) params.set("end", endDate);
      const { data } = await api.get<APIResponse<InterMonthReport>>(
        `/reports/inter-month/${selectedPropertyId}?${params}`
      );
      return data.data;
    },
    enabled: !!selectedPropertyId,
  });
}

export function useLineItemChildren(parentId: string | null, period: string) {
  const { selectedPropertyId } = useProperty();
  const { getToken } = useAuth();
  const api = createApiClient(getToken);

  return useQuery({
    queryKey: [
      "inter-month-children",
      selectedPropertyId,
      parentId,
      period,
    ],
    queryFn: async () => {
      const { data } = await api.get<APIResponse<ReportLineItem[]>>(
        `/reports/inter-month/${selectedPropertyId}/children/${parentId}?period=${period}`
      );
      return data.data;
    },
    enabled: !!selectedPropertyId && !!parentId,
  });
}
