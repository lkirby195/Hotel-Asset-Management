"use client";

import { PropertySelector } from "@/components/layout/property-selector";
import type { ReactNode } from "react";

interface ContentHeaderProps {
  title: string;
  subtitle?: string;
  showPropertySelector?: boolean;
  children?: ReactNode;
}

export function ContentHeader({
  title,
  subtitle,
  showPropertySelector = true,
  children,
}: ContentHeaderProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-medium text-gray-900">{title}</h1>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>
          )}
        </div>
        {showPropertySelector && <PropertySelector />}
      </div>
      {children && <div className="flex items-center justify-between">{children}</div>}
    </div>
  );
}
