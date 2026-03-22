import type { DisplayFormat } from '@/types/reports';
import {
  formatCurrency,
  formatVarianceCurrency,
  formatPercent,
  formatVariancePercent,
  formatPercentagePoints,
  formatInteger,
  formatVarianceInteger,
  formatDecimal,
  formatVarianceDecimal,
} from './formatters';

/**
 * Auto-format a value based on its display format.
 * Falls back to currency if no format is specified.
 */
export function autoFormat(
  value: number,
  format: DisplayFormat = 'currency'
): string {
  switch (format) {
    case 'currency':
      return formatCurrency(value);
    case 'percentage':
      return formatPercent(value);
    case 'integer':
      return formatInteger(value);
    case 'decimal':
      return formatDecimal(value);
  }
}

/**
 * Auto-format a variance value based on its display format.
 * Falls back to currency if no format is specified.
 */
export function autoFormatVariance(
  value: number,
  format: DisplayFormat = 'currency'
): string {
  switch (format) {
    case 'currency':
      return formatVarianceCurrency(value);
    case 'percentage':
      return formatPercentagePoints(value);
    case 'integer':
      return formatVarianceInteger(value);
    case 'decimal':
      return formatVarianceDecimal(value);
  }
}

/**
 * Infer display format from a line item's data_type when display_format is not set.
 */
export function inferDisplayFormat(
  dataType: string,
  displayFormat?: DisplayFormat
): DisplayFormat {
  if (displayFormat) return displayFormat;
  switch (dataType) {
    case 'percentage':
      return 'percentage';
    case 'metric':
      return 'integer';
    default:
      return 'currency';
  }
}
