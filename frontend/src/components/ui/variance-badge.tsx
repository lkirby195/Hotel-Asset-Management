import { cn } from "@/lib/utils";

interface VarianceBadgeProps {
  value: number;
  label: string;
  /** Override automatic color detection (e.g., for expense metrics where negative is good) */
  favorable?: boolean;
  className?: string;
}

export function VarianceBadge({ value, label, favorable, className }: VarianceBadgeProps) {
  const isFavorable = favorable ?? value > 0;
  const isNeutral = value === 0;

  return (
    <span
      className={cn(
        "inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium",
        isNeutral
          ? "text-surface-500 bg-surface-100"
          : isFavorable
            ? "text-positive-700 bg-positive-50"
            : "text-negative-700 bg-negative-50",
        className,
      )}
    >
      {label}
    </span>
  );
}
