const currencyFormatterFull = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

export function formatCurrency(cents: number): string {
  const dollars = cents / 100;
  if (Math.abs(dollars) >= 1_000_000) {
    return `$${(dollars / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(dollars) >= 10_000) {
    return `$${(dollars / 1_000).toFixed(0)}K`;
  }
  return currencyFormatterFull.format(dollars);
}

export function formatVarianceCurrency(cents: number): string {
  const formatted = formatCurrency(Math.abs(cents));
  if (cents > 0) return `+${formatted}`;
  if (cents < 0) return `-${formatted}`;
  return formatted;
}

export function formatPercent(decimal: number): string {
  return `${(decimal * 100).toFixed(1)}%`;
}

export function formatVariancePercent(decimal: number): string {
  const pct = (decimal * 100).toFixed(1);
  if (decimal > 0) return `+${pct}%`;
  if (decimal < 0) return `${pct}%`;
  return `${pct}%`;
}

export function formatPercentagePoints(decimal: number): string {
  const pp = (decimal * 100).toFixed(1);
  if (decimal > 0) return `+${pp}pp`;
  if (decimal < 0) return `${pp}pp`;
  return `${pp}pp`;
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
