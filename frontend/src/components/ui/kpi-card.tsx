import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  label: string;
  value: string;
  subtitle?: string;
  children?: ReactNode;
  className?: string;
}

export function KpiCard({ label, value, subtitle, children, className }: KpiCardProps) {
  return (
    <div className={cn("kpi-card bg-white rounded-xl border border-surface-200 p-4 min-h-[140px] flex flex-col", className)}>
      <div className="text-xs font-medium text-surface-400 mb-1">{label}</div>
      <div className="text-2xl font-bold text-surface-900 tabular-nums">{value}</div>
      {subtitle && (
        <div className="text-xs text-surface-500 mt-0.5">{subtitle}</div>
      )}
      <div className="flex items-center gap-2 mt-auto pt-2 flex-wrap">
        {children ?? <span className="text-xs text-surface-300">&mdash;</span>}
      </div>
    </div>
  );
}
