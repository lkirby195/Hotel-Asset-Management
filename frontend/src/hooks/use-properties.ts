"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import type { APIResponse, Property } from "@/lib/types";

export function useProperties() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);

  return useQuery({
    queryKey: ["properties"],
    queryFn: async () => {
      const { data } = await api.get<APIResponse<Property[]>>("/properties");
      return data.data;
    },
  });
}
