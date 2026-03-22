"use client";

import { cn } from "@/lib/utils";
import type { MonthStatus, GoalComparisonType, GoalDisplayFormat } from "@/types/goals";

const MONTH_NAMES = [
  "", "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

interface MonthlyRingProps {
  month: number;
  status: MonthStatus;
  actual?: number | null;
  target: number;
  percentOfGoal?: number | null;
  format: GoalDisplayFormat;
  comparisonType: GoalComparisonType;
  isOverridden: boolean;
}

function getRingColor(percent: number, comparisonType: GoalComparisonType): string {
  const effective = comparisonType === "lte" ? 2 - percent : percent;
  if (effective < 0.5) return "#EF4444";
  if (effective < 0.8) return "#F59E0B";
  return "#22C55E";
}

function formatCompact(value: number, format: GoalDisplayFormat): string {
  if (format === "percentage") return `${(value / 100).toFixed(1)}%`;
  const dollars = value / 100;
  if (Math.abs(dollars) >= 1_000_000) return `$${(dollars / 1_000_000).toFixed(1)}M`;
  if (Math.abs(dollars) >= 1_000) return `$${(dollars / 1_000).toFixed(0)}K`;
  return `$${dollars.toFixed(0)}`;
}

export function MonthlyRing({
  month,
  status,
  actual,
  target,
  percentOfGoal,
  format,
  comparisonType,
  isOverridden,
}: MonthlyRingProps) {
  const size = 60;
  const strokeWidth = 5;
  const r = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;

  const pct = percentOfGoal ?? 0;
  const progress = Math.min(Math.max(pct, 0), 1.1);
  const strokeDash = progress * circumference;

  const ringColor =
    status === "current"
      ? "#2563EB"
      : status === "completed"
        ? getRingColor(pct, comparisonType)
        : "#E5E7EB";

  return (
    <div
      className={cn(
        "bg-white border border-gray-200 rounded-lg p-3 text-center",
        status === "not_started" && "opacity-60"
      )}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className={cn("mx-auto", status === "current" && "animate-pulse-subtle")}
      >
        {/* Background ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="#E5E7EB"
          strokeWidth={strokeWidth}
        />
        {/* Progress ring */}
        {status !== "not_started" && (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={ringColor}
            strokeWidth={strokeWidth}
            strokeDasharray={`${strokeDash} ${circumference}`}
            strokeLinecap="round"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        )}
        {/* Center text */}
        <text
          x={size / 2}
          y={size / 2}
          textAnchor="middle"
          dominantBaseline="central"
          fill={status === "not_started" ? "#9CA3AF" : "#111827"}
          fontSize={12}
          fontWeight={600}
        >
          {status === "not_started" ? "--" : `${Math.round(pct * 100)}%`}
        </text>
      </svg>

      <div className="mt-1.5">
        <div className="text-xs font-medium text-gray-900">
          {MONTH_NAMES[month]}
          {isOverridden && <span className="text-brand ml-0.5">*</span>}
        </div>
        <div className="text-[10px] tabular-nums text-gray-500">
          {status === "not_started" ? (
            "Not started"
          ) : (
            `${formatCompact(actual ?? 0, format)} / ${formatCompact(target, format)}`
          )}
        </div>
      </div>
    </div>
  );
}
