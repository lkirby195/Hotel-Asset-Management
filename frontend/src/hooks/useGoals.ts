"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import { MOCK_GOALS_RESPONSE } from "@/lib/mock/goals-data";
import type { GoalsResponse, GoalInput, AvailableMetric } from "@/types/goals";
import type { APIResponse } from "@/lib/types";

// TODO: Remove when API is ready
const USE_MOCK_GOALS = true;

export function useGoals() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);

  return useQuery({
    queryKey: ["goals"],
    queryFn: async (): Promise<GoalsResponse> => {
      if (USE_MOCK_GOALS) return MOCK_GOALS_RESPONSE;
      const { data } = await api.get<APIResponse<GoalsResponse>>("/goals");
      return data.data;
    },
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}

export function useSetGoals() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (goals: GoalInput[]) => {
      const { data } = await api.put<APIResponse<GoalsResponse>>("/goals", { goals });
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
    },
  });
}

export function useAvailableMetrics() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);

  return useQuery({
    queryKey: ["goals", "available-metrics"],
    queryFn: async (): Promise<AvailableMetric[]> => {
      const { data } = await api.get<APIResponse<{ metrics: AvailableMetric[] }>>("/goals/available-metrics");
      return data.data.metrics;
    },
    staleTime: 30 * 60 * 1000,
  });
}
