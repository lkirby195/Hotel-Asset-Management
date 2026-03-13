"use client";

import { cn } from "@/lib/utils";

type BadgeStatus = "closed" | "open" | "synced" | "error";

interface StatusBadgeProps {
  status: BadgeStatus;
  label?: string;
}

const STATUS_STYLES: Record<BadgeStatus, string> = {
  closed: "bg-favorable-bg text-favorable-dark",
  open: "bg-warning-bg text-warning-dark",
  synced: "bg-brand-light text-brand",
  error: "bg-unfavorable-bg text-unfavorable-dark",
};

const STATUS_LABELS: Record<BadgeStatus, string> = {
  closed: "Closed",
  open: "Open",
  synced: "Synced",
  error: "Error",
};

export function StatusBadge({ status, label }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "text-xs px-2.5 py-0.5 rounded-full font-medium",
        STATUS_STYLES[status]
      )}
    >
      {label ?? STATUS_LABELS[status]}
    </span>
  );
}
