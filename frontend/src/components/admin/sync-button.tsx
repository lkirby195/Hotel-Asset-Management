"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAdminSync } from "@/hooks/use-admin-sync";
import { cn } from "@/lib/utils";

export function SyncButton() {
  const { triggerSync, isPending } = useAdminSync();
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const handleSync = async () => {
    setSyncing(true);
    setMessage(null);
    try {
      await triggerSync();
      setMessage({ type: "success", text: "Sync completed successfully." });
    } catch {
      setMessage({ type: "error", text: "Sync failed. Please try again." });
    } finally {
      setSyncing(false);
    }
  };

  const isDisabled = isPending || syncing;

  return (
    <div className="space-y-3">
      <Button onClick={handleSync} disabled={isDisabled}>
        <RefreshCw
          className={cn("mr-2 h-4 w-4", syncing && "animate-spin")}
        />
        {syncing ? "Syncing..." : "Trigger Sync"}
      </Button>
      {message && (
        <p
          className={cn(
            "text-sm",
            message.type === "success" ? "text-green-600" : "text-red-600"
          )}
        >
          {message.text}
        </p>
      )}
    </div>
  );
}
