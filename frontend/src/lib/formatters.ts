const currencyFormatterFull = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

function wrapNegative(formatted: string, isNegative: boolean): string {
  return isNegative ? `(${formatted})` : formatted;
}

export function formatCurrency(cents: number): string {
  const dollars = Math.abs(cents) / 100;
  const isNeg = cents < 0;
  if (dollars >= 1_000_000) {
    return wrapNegative(`$${(dollars / 1_000_000).toFixed(1)}M`, isNeg);
  }
  if (dollars >= 10_000) {
    return wrapNegative(`$${(dollars / 1_000).toFixed(0)}K`, isNeg);
  }
  return wrapNegative(currencyFormatterFull.format(dollars), isNeg);
}

export function formatVarianceCurrency(cents: number): string {
  const formatted = formatCurrency(Math.abs(cents));
  if (cents > 0) return `+${formatted}`;
  if (cents < 0) return `(${formatted})`;
  return formatted;
}

export function formatPercent(decimal: number): string {
  const pct = Math.abs(decimal * 100).toFixed(1);
  return decimal < 0 ? `(${pct}%)` : `${pct}%`;
}

export function formatVariancePercent(decimal: number): string {
  const pct = Math.abs(decimal * 100).toFixed(1);
  if (decimal > 0) return `+${pct}%`;
  if (decimal < 0) return `(${pct}%)`;
  return `${pct}%`;
}

export function formatPercentagePoints(decimal: number): string {
  const pp = Math.abs(decimal * 100).toFixed(1);
  if (decimal > 0) return `+${pp}pp`;
  if (decimal < 0) return `(${pp}pp)`;
  return `${pp}pp`;
}

export function formatInteger(value: number): string {
  const abs = Math.abs(value);
  const formatted = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(abs);
  return value < 0 ? `(${formatted})` : formatted;
}

export function formatVarianceInteger(value: number): string {
  const formatted = formatInteger(Math.abs(value));
  if (value > 0) return `+${formatted}`;
  if (value < 0) return `(${formatted})`;
  return formatted;
}

export function formatDecimal(value: number): string {
  const abs = Math.abs(value);
  const formatted = abs.toFixed(1);
  return value < 0 ? `(${formatted})` : formatted;
}

export function formatVarianceDecimal(value: number): string {
  const formatted = formatDecimal(Math.abs(value));
  if (value > 0) return `+${formatted}`;
  if (value < 0) return `(${formatted})`;
  return formatted;
}

export function getVarianceColor(
  value: number,
  dataType: 'revenue' | 'expense' | 'metric' | 'percentage'
): string {
  if (value === 0) return 'text-gray-500';
  const isExpense = dataType === 'expense';
  const isFavorable = isExpense ? value < 0 : value > 0;
  return isFavorable ? 'text-favorable' : 'text-unfavorable';
}
