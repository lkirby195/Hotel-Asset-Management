"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import { useProperty } from "@/providers/property-provider";
import type { ApiResponse } from "@/types/api";

export interface CommentaryItem {
  id: string;
  tenant_id: string;
  property_id: string;
  user_id: string;
  user_name: string;
  year: number;
  month: number;
  department_tag: string | null;
  category_tag: string;
  text: string;
  created_at: string;
  updated_at: string;
}

export interface CommentaryCreateInput {
  year: number;
  month: number;
  department_tag?: string | null;
  category_tag: string;
  text: string;
}

export function useCommentary(year: number, month: number) {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const { selectedPropertyId } = useProperty();

  return useQuery<CommentaryItem[]>({
    queryKey: ["commentary", selectedPropertyId, year, month],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<CommentaryItem[]>>(
        `/commentary/${selectedPropertyId}?year=${year}&month=${month}`,
      );
      return data.data;
    },
    enabled: !!selectedPropertyId && year > 0 && month > 0,
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateCommentary() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const { selectedPropertyId } = useProperty();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: CommentaryCreateInput) => {
      const { data } = await api.post<ApiResponse<CommentaryItem>>(
        `/commentary/${selectedPropertyId}`,
        input,
      );
      return data.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["commentary", selectedPropertyId, variables.year, variables.month],
      });
    },
  });
}

export function useDeleteCommentary() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const { selectedPropertyId } = useProperty();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (commentId: string) => {
      await api.delete(`/commentary/${commentId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["commentary", selectedPropertyId] });
    },
  });
}
