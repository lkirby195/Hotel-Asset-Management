"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import type { ApiResponse } from "@/types/api";

interface UserMe {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  property_ids: string[];
}

export function useRole() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);

  const { data } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<UserMe>>("/auth/me");
      return data.data;
    },
  });

  return {
    role: data?.role ?? "manager",
    isAdmin: data?.role === "admin",
    isExecutive: data?.role === "executive" || data?.role === "admin",
    user: data ?? null,
  };
}
