"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import type { APIResponse, UserProfile } from "@/lib/types";

export function useUsers() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);

  return useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => {
      const { data } = await api.get<APIResponse<UserProfile[]>>(
        "/admin/users"
      );
      return data.data;
    },
  });
}

export function useCreateUser() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: {
      clerk_id: string;
      email: string;
      name: string;
      role: string;
      property_ids: string[];
    }) => {
      const { data } = await api.post<APIResponse<UserProfile>>(
        "/admin/users",
        body
      );
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });
}

export function useUpdateUser() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      userId,
      body,
    }: {
      userId: string;
      body: {
        email?: string;
        name?: string;
        role?: string;
        is_active?: boolean;
        property_ids?: string[];
      };
    }) => {
      const { data } = await api.put<APIResponse<UserProfile>>(
        `/admin/users/${userId}`,
        body
      );
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });
}

export function useDeleteUser() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userId: string) => {
      await api.delete(`/admin/users/${userId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });
}
