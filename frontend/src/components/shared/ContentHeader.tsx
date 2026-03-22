"use client";

import { PropertySelector } from "@/components/layout/property-selector";
import type { ReactNode } from "react";

interface ContentHeaderProps {
  title: string;
  subtitle?: string;
  showPropertySelector?: boolean;
  children?: ReactNode;
  lastSynced?: string;
}

export function ContentHeader({
  title,
  subtitle,
  showPropertySelector = true,
  children,
  lastSynced,
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
      {children && (
        <div className="flex items-center gap-4 bg-white border border-gray-200 rounded-lg px-3 py-2">
          {children}
          {lastSynced && (
            <>
              <div className="h-6 w-px bg-gray-200 ml-auto" />
              <span className="text-xs text-gray-400 whitespace-nowrap">
                Last synced: {lastSynced}
              </span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
