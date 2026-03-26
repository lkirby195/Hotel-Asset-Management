"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import { useProperty } from "@/providers/property-provider";
import type { ApiResponse } from "@/types/api";

export interface GoalFromAPI {
  id: string;
  tenant_id: string;
  property_id: string;
  user_id: string;
  metric_code: string;
  target_value: number;
  period_type: string;
  year: number;
  month: number | null;
  created_at: string;
  updated_at: string;
}

export interface GoalCreateInput {
  metric_code: string;
  target_value: number;
  period_type: string;
  year: number;
  month?: number | null;
}

export interface GoalUpdateInput {
  target_value?: number;
  metric_code?: string;
  period_type?: string;
  year?: number;
  month?: number | null;
}

export function useGoals(year?: number) {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const { selectedPropertyId } = useProperty();

  return useQuery<GoalFromAPI[]>({
    queryKey: ["goals", selectedPropertyId, year],
    queryFn: async () => {
      const params = year ? `?year=${year}` : "";
      const { data } = await api.get<ApiResponse<GoalFromAPI[]>>(
        `/goals/${selectedPropertyId}${params}`,
      );
      return data.data;
    },
    enabled: !!selectedPropertyId,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateGoal() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const { selectedPropertyId } = useProperty();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: GoalCreateInput) => {
      const { data } = await api.post<ApiResponse<GoalFromAPI>>(
        `/goals/${selectedPropertyId}`,
        input,
      );
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals", selectedPropertyId] });
    },
  });
}

export function useUpdateGoal() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const { selectedPropertyId } = useProperty();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ goalId, input }: { goalId: string; input: GoalUpdateInput }) => {
      const { data } = await api.put<ApiResponse<GoalFromAPI>>(
        `/goals/${goalId}`,
        input,
      );
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals", selectedPropertyId] });
    },
  });
}

export function useDeleteGoal() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const { selectedPropertyId } = useProperty();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (goalId: string) => {
      await api.delete(`/goals/${goalId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals", selectedPropertyId] });
    },
  });
}
