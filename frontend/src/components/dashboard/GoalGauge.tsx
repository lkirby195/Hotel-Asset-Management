"use client";

import type { ComparisonType } from "@/types/goals";

interface GoalGaugeProps {
  label: string;
  current_value: number;
  target_value: number;
  percent_of_goal: number;
  format: "currency" | "percentage";
  comparison_type: ComparisonType;
}

function getGaugeColor(percent: number, comparison: ComparisonType): string {
  const effective = comparison === "lte" ? 2 - percent : percent;
  if (effective < 0.5) return "#EF4444";
  if (effective < 0.8) return "#F59E0B";
  return "#22C55E";
}

function formatGaugeValue(value: number, format: "currency" | "percentage"): string {
  if (format === "percentage") return `${(value * 100).toFixed(1)}%`;
  const dollars = value / 100;
  if (Math.abs(dollars) >= 1_000_000) return `$${(dollars / 1_000_000).toFixed(1)}M`;
  if (Math.abs(dollars) >= 1_000) return `$${(dollars / 1_000).toFixed(0)}K`;
  return `$${dollars.toFixed(0)}`;
}

export function GoalGauge({
  label,
  current_value,
  target_value,
  percent_of_goal,
  format,
  comparison_type,
}: GoalGaugeProps) {
  const color = getGaugeColor(percent_of_goal, comparison_type);
  const capped = Math.min(percent_of_goal, 1.1);

  // Arc calculations for half-circle
  const cx = 100, cy = 100, r = 80;
  const startAngle = Math.PI;
  const endAngle = 0;
  const progressAngle = startAngle - capped * Math.PI;

  const bgStartX = cx + r * Math.cos(startAngle);
  const bgStartY = cy - r * Math.sin(startAngle);
  const bgEndX = cx + r * Math.cos(endAngle);
  const bgEndY = cy - r * Math.sin(endAngle);

  const progEndX = cx + r * Math.cos(progressAngle);
  const progEndY = cy - r * Math.sin(progressAngle);
  const largeArc = capped > 0.5 ? 1 : 0;

  // Needle
  const needleAngle = startAngle - capped * Math.PI;
  const needleX = cx + (r - 10) * Math.cos(needleAngle);
  const needleY = cy - (r - 10) * Math.sin(needleAngle);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
      <svg viewBox="0 0 200 115" className="mx-auto w-[200px] h-[110px]">
        {/* Background arc */}
        <path
          d={`M ${bgStartX} ${bgStartY} A ${r} ${r} 0 0 1 ${bgEndX} ${bgEndY}`}
          fill="none"
          stroke="#E5E7EB"
          strokeWidth={12}
          strokeLinecap="round"
        />
        {/* Progress arc */}
        {capped > 0 && (
          <path
            d={`M ${bgStartX} ${bgStartY} A ${r} ${r} 0 ${largeArc} 1 ${progEndX} ${progEndY}`}
            fill="none"
            stroke={color}
            strokeWidth={12}
            strokeLinecap="round"
          />
        )}
        {/* Needle */}
        <line
          x1={cx}
          y1={cy}
          x2={needleX}
          y2={needleY}
          stroke="#111827"
          strokeWidth={2.5}
          strokeLinecap="round"
        />
        {/* Center dot */}
        <circle cx={cx} cy={cy} r={4} fill="#111827" />
      </svg>
      <div className="mt-1">
        <span className="text-base font-medium text-gray-900">
          {formatGaugeValue(current_value, format)}
        </span>
        <span className="text-xs text-gray-500">
          {" "}/ {formatGaugeValue(target_value, format)}
        </span>
      </div>
      <div className="text-xs text-gray-500">
        {(percent_of_goal * 100).toFixed(1)}% of goal
      </div>
      <div className="text-xs text-gray-500 mt-1 font-medium">{label}</div>
    </div>
  );
}
