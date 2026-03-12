"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "@/lib/api-client";
import type { APIResponse } from "@/lib/types";

export function useAdminSync() {
  const { getToken } = useAuth();
  const api = createApiClient(getToken);
  const queryClient = useQueryClient();

  const syncMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<
        APIResponse<{ task_id: string; status: string }>
      >("/admin/sync");
      return data.data;
    },
  });

  const pollStatus = async (taskId: string): Promise<string> => {
    const { data } = await api.get<
      APIResponse<{ task_id: string; status: string }>
    >(`/admin/sync/${taskId}`);
    return data.data.status;
  };

  const triggerSync = async () => {
    const result = await syncMutation.mutateAsync();
    // Poll until complete
    return new Promise<void>((resolve, reject) => {
      const interval = setInterval(async () => {
        try {
          const status = await pollStatus(result.task_id);
          if (status === "SUCCESS") {
            clearInterval(interval);
            queryClient.invalidateQueries();
            resolve();
          } else if (status === "FAILURE") {
            clearInterval(interval);
            reject(new Error("Sync failed"));
          }
        } catch {
          clearInterval(interval);
          reject(new Error("Failed to check sync status"));
        }
      }, 2000);
    });
  };

  return {
    triggerSync,
    isPending: syncMutation.isPending,
  };
}
