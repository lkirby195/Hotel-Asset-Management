"use client";

import { ContentHeader } from "@/components/shared/ContentHeader";
import { SyncButton } from "@/components/admin/sync-button";
import { MonthCloseToggle } from "@/components/admin/MonthCloseToggle";

export default function AdminSyncPage() {
  return (
    <div className="space-y-8">
      <ContentHeader title="Data sync" showPropertySelector={false} />

      <section className="space-y-4">
        <h2 className="text-base font-medium text-gray-900">Sync controls</h2>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="mb-4 text-sm text-gray-500">
            Trigger a full data sync from ProfitSword. This pulls the current
            and prior month actuals, budgets, and forecasts for all properties,
            refreshes materialized views, and invalidates the cache.
          </p>
          <SyncButton />
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-base font-medium text-gray-900">Month close</h2>
        <MonthCloseToggle />
      </section>
    </div>
  );
}
