"use client";

import { ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { GoalComparisonType, GoalDisplayFormat } from "@/types/goals";

interface GoalGaugeProps {
  label: string;
  current_value: number;
  target_value: number;
  percent_of_goal: number;
  format: GoalDisplayFormat;
  comparison_type: GoalComparisonType;
  isExpanded?: boolean;
  onClick?: () => void;
}

function getGaugeColor(percent: number, comparison: GoalComparisonType): string {
  const effective = comparison === "lte" ? 2 - percent : percent;
  if (effective < 0.5) return "#EF4444";
  if (effective < 0.8) return "#F59E0B";
  return "#22C55E";
}

function formatGaugeValue(value: number, format: GoalDisplayFormat): string {
  if (format === "percentage") {
    const pct = value / 100;
    return `${pct.toFixed(1)}%`;
  }
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
  isExpanded = false,
  onClick,
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

  // Tick marks at 25%, 50%, 75%
  const ticks = [0.25, 0.5, 0.75];
  const tickInner = r - 10;
  const tickOuter = r + 10;
  const labelRadius = r + 20;

  const ExpandIcon = isExpanded ? ChevronUp : ChevronDown;

  return (
    <div
      className={cn(
        "bg-white border rounded-lg p-4 text-center transition-colors",
        onClick && "cursor-pointer hover:border-brand",
        isExpanded ? "border-brand" : "border-gray-200"
      )}
      onClick={onClick}
    >
      <div className="text-[10px] font-medium uppercase tracking-wider text-gray-400 mb-0.5">
        Annual
      </div>
      <div className="text-xs font-medium text-gray-900 mb-1">{label}</div>

      <svg viewBox="0 -5 200 120" className="mx-auto w-[200px] h-[115px]">
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
        {/* Tick marks and labels */}
        {ticks.map((pct) => {
          const angle = Math.PI - pct * Math.PI;
          const x1 = cx + tickInner * Math.cos(angle);
          const y1 = cy - tickInner * Math.sin(angle);
          const x2 = cx + tickOuter * Math.cos(angle);
          const y2 = cy - tickOuter * Math.sin(angle);
          const lx = cx + labelRadius * Math.cos(angle);
          const ly = cy - labelRadius * Math.sin(angle);
          return (
            <g key={pct}>
              <line
                x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="#6B7280"
                strokeWidth={2.5}
                strokeLinecap="round"
              />
              <text
                x={lx} y={ly}
                textAnchor="middle"
                dominantBaseline="central"
                fill="#6B7280"
                fontSize={9}
                fontWeight={700}
              >
                {pct * 100}%
              </text>
            </g>
          );
        })}
        {/* Needle */}
        <line
          x1={cx} y1={cy} x2={needleX} y2={needleY}
          stroke="#111827"
          strokeWidth={2.5}
          strokeLinecap="round"
        />
        {/* Center dot */}
        <circle cx={cx} cy={cy} r={4} fill="#111827" />
      </svg>

      <div className="mt-1">
        <span className="text-base font-medium tabular-nums text-gray-900">
          {formatGaugeValue(current_value, format)}
        </span>
        <span className="text-xs text-gray-500">
          {" "}/ {formatGaugeValue(target_value, format)}
        </span>
      </div>
      <div className="text-xs tabular-nums text-gray-500">
        {(percent_of_goal * 100).toFixed(1)}% of goal
      </div>
      {onClick && (
        <ExpandIcon className="mx-auto mt-1 h-3 w-3 text-gray-400" />
      )}
    </div>
  );
}
