"use client";

import { cn } from "@/lib/utils";
import { COMPARISON_OPTIONS } from "@/lib/constants";
import type { ComparisonType } from "@/types/reports";

interface ComparisonSelectorProps {
  selected: Set<ComparisonType>;
  onChange: (type: ComparisonType) => void;
}

export function ComparisonSelector({ selected, onChange }: ComparisonSelectorProps) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-xs text-gray-500 mr-1">Compare:</span>
      {COMPARISON_OPTIONS.map((opt) => {
        const isActive = selected.has(opt.value);
        return (
          <button
            key={opt.value}
            className={cn(
              "rounded-full px-3.5 py-1 text-xs font-medium transition-colors",
              isActive
                ? "bg-brand text-white"
                : "bg-white text-gray-500 border border-gray-200 hover:border-gray-300 cursor-pointer"
            )}
            onClick={() => onChange(opt.value)}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
