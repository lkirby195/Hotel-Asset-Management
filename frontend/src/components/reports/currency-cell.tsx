"use client";

import { formatCurrency } from "@/lib/utils";

interface CurrencyCellProps {
  value: number | null;
}

export function CurrencyCell({ value }: CurrencyCellProps) {
  return (
    <td className="px-3 py-2 text-right tabular-nums">
      {value !== null && value !== undefined ? formatCurrency(value) : "—"}
    </td>
  );
}
