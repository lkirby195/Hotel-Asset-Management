"use client";

import { Skeleton } from "@/components/ui/skeleton";

export function KpiSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="bg-white border border-gray-200 rounded-lg p-3 space-y-2">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-7 w-24" />
          <Skeleton className="h-3 w-20" />
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 8 }: { rows?: number }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="bg-surface px-3 py-3">
        <Skeleton className="h-4 w-full" />
      </div>
      <div className="divide-y divide-gray-100">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="px-3 py-3">
            <Skeleton className="h-5 w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function GaugeSkeleton() {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 text-center space-y-3">
      <Skeleton className="h-[110px] w-[200px] mx-auto rounded-full" />
      <Skeleton className="h-4 w-20 mx-auto" />
      <Skeleton className="h-3 w-24 mx-auto" />
    </div>
  );
}
