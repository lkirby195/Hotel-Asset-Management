"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { PeriodType } from "@/types/reports";

const PERIODS: { value: PeriodType; label: string }[] = [
  { value: "mtd", label: "MTD" },
  { value: "qtd", label: "QTD" },
  { value: "ytd", label: "YTD" },
  { value: "t28", label: "T28" },
  { value: "weekly", label: "Weekly" },
  { value: "custom", label: "Custom" },
];

interface PeriodSelectorProps {
  selected: PeriodType;
  onChange: (period: PeriodType) => void;
  onCustomRange?: (start: string, end: string) => void;
  exclude?: PeriodType[];
}

export function PeriodSelector({
  selected,
  onChange,
  onCustomRange,
  exclude = [],
}: PeriodSelectorProps) {
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const filtered = PERIODS.filter((p) => !exclude.includes(p.value));

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {filtered.map((p) => (
        <button
          key={p.value}
          className={cn(
            "rounded-full px-3 py-1 text-xs font-medium transition-colors border",
            selected === p.value
              ? "bg-brand text-white border-brand"
              : "bg-white text-gray-500 border-gray-200 hover:border-gray-300"
          )}
          onClick={() => {
            if (p.value === "custom") {
              setShowDatePicker(true);
              onChange(p.value);
            } else {
              setShowDatePicker(false);
              onChange(p.value);
            }
          }}
        >
          {p.label}
        </button>
      ))}

      {showDatePicker && selected === "custom" && (
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="rounded-md border border-gray-200 px-2 py-1 text-xs"
          />
          <span className="text-xs text-gray-500">to</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="rounded-md border border-gray-200 px-2 py-1 text-xs"
          />
          <button
            className="rounded-md bg-brand px-3 py-1 text-xs text-white"
            onClick={() => {
              if (startDate && endDate && onCustomRange) {
                onCustomRange(startDate, endDate);
              }
            }}
          >
            Apply
          </button>
        </div>
      )}
    </div>
  );
}
