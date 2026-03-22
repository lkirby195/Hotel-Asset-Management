import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Re-export formatters for backward compatibility with existing components
export { formatCurrency, formatVarianceCurrency } from "./formatters";

export function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return "\u2014";
  if (value < 0) return `(${Math.abs(value).toFixed(1)}%)`;
  return `+${value.toFixed(1)}%`;
}
