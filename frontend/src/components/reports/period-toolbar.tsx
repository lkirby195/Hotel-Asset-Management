"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { PERIODS } from "@/lib/constants";
import type { Period } from "@/lib/types";

interface PeriodToolbarProps {
  value: Period;
  onChange: (period: Period, start?: string, end?: string) => void;
}

export function PeriodToolbar({ value, onChange }: PeriodToolbarProps) {
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  return (
    <div className="flex items-center gap-2">
      {PERIODS.map((p) => (
        <button
          key={p.value}
          className={cn(
            "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
            value === p.value
              ? "bg-gray-900 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          )}
          onClick={() => {
            if (p.value === "custom") {
              setShowDatePicker(true);
            } else {
              setShowDatePicker(false);
              onChange(p.value);
            }
          }}
        >
          {p.label}
        </button>
      ))}

      {showDatePicker && (
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="rounded border px-2 py-1 text-sm"
          />
          <span className="text-sm text-gray-500">to</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="rounded border px-2 py-1 text-sm"
          />
          <button
            className="rounded bg-gray-900 px-3 py-1 text-sm text-white"
            onClick={() => {
              if (startDate && endDate) {
                onChange("custom", startDate, endDate);
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
