import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface DataTableProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export function DataTable({ title, children, className }: DataTableProps) {
  return (
    <div className={cn("bg-white rounded-xl border border-surface-200 overflow-hidden", className)}>
      {title && (
        <div className="px-4 py-3 border-b border-surface-100 flex items-center justify-between">
          <span className="text-xs font-semibold text-surface-500 uppercase tracking-wider">
            {title}
          </span>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">{children}</table>
      </div>
    </div>
  );
}

export function TableHeader({ children }: { children: ReactNode }) {
  return (
    <thead>
      <tr className="bg-surface-50 border-b border-surface-200">{children}</tr>
    </thead>
  );
}

export function Th({
  children,
  align = "right",
  className,
}: {
  children: ReactNode;
  align?: "left" | "right" | "center";
  className?: string;
}) {
  return (
    <th
      className={cn(
        "py-3 px-4 text-xs font-semibold text-surface-500 uppercase tracking-wider",
        align === "left" ? "text-left" : align === "center" ? "text-center" : "text-right",
        className,
      )}
    >
      {children}
    </th>
  );
}
