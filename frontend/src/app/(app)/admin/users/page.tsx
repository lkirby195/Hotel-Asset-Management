"use client";

import { ContentHeader } from "@/components/shared/ContentHeader";
import { UserTable } from "@/components/admin/user-table";

export default function AdminUsersPage() {
  return (
    <div className="space-y-6">
      <ContentHeader title="User management" />
      <UserTable />
    </div>
  );
}
