"use client";

import { SyncButton } from "@/components/admin/sync-button";
import { UserTable } from "@/components/admin/user-table";

export default function AdminPage() {
  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Admin Panel</h1>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Data Sync</h2>
        <div className="rounded-lg border bg-white p-6">
          <p className="mb-4 text-sm text-gray-600">
            Trigger a full data sync from ProfitSword. This pulls the current
            and prior month actuals, budgets, and forecasts for all properties,
            refreshes materialized views, and invalidates the cache.
          </p>
          <SyncButton />
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold">User Management</h2>
        <UserTable />
      </section>
    </div>
  );
}
