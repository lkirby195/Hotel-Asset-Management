"use client";

import { useState } from "react";

interface DateRangePickerProps {
  onApply: (start: string, end: string) => void;
  initialStart?: string;
  initialEnd?: string;
}

export function DateRangePicker({
  onApply,
  initialStart = "",
  initialEnd = "",
}: DateRangePickerProps) {
  const [start, setStart] = useState(initialStart);
  const [end, setEnd] = useState(initialEnd);

  return (
    <div className="flex items-center gap-2">
      <input
        type="date"
        value={start}
        onChange={(e) => setStart(e.target.value)}
        className="rounded-md border border-gray-200 px-2 py-1 text-xs"
      />
      <span className="text-xs text-gray-500">to</span>
      <input
        type="date"
        value={end}
        onChange={(e) => setEnd(e.target.value)}
        className="rounded-md border border-gray-200 px-2 py-1 text-xs"
      />
      <button
        className="rounded-md bg-brand px-3 py-1 text-xs font-medium text-white hover:bg-brand-dark"
        onClick={() => {
          if (start && end) onApply(start, end);
        }}
        disabled={!start || !end}
      >
        Apply
      </button>
    </div>
  );
}
