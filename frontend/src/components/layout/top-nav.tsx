"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";
import { Building2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useProperty } from "@/providers/property-provider";
import { PLATFORM_NAME } from "@/lib/constants";

const DEV_AUTH_BYPASS = process.env.NEXT_PUBLIC_DEV_AUTH_BYPASS === "true";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "P&L", href: "/pl" },
  { label: "Departments", href: "/departments" },
  { label: "Pace", href: "/sales-performance" },
  { label: "Goals", href: "/goals" },
];

const TIME_FRAMES = ["Daily", "Weekly", "Monthly", "T28", "RoY", "Annual"] as const;

export function TopNav() {
  const pathname = usePathname();
  const { properties, selectedPropertyId, setSelectedPropertyId } = useProperty();

  return (
    <nav className="bg-white border-b border-surface-200 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
      {/* Left: Brand + Nav tabs */}
      <div className="flex items-center gap-6">
        <h1 className="text-lg font-bold text-surface-900">{PLATFORM_NAME}</h1>
        <div className="flex gap-1 text-sm">
          {NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "px-3 py-1.5 rounded-md transition-colors",
                  isActive
                    ? "bg-brand-50 text-brand-700 font-medium"
                    : "text-surface-500 hover:text-surface-700",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Right: Property selector + Time frame + User */}
      <div className="flex items-center gap-4">
        {/* Property Selector */}
        <div className="flex items-center gap-2 bg-surface-50 border border-surface-200 rounded-lg px-3 py-1.5">
          <Building2 className="w-4 h-4 text-surface-400" />
          <select
            className="bg-transparent text-sm font-medium text-surface-700 outline-none cursor-pointer"
            value={selectedPropertyId ?? ""}
            onChange={(e) => e.target.value && setSelectedPropertyId(e.target.value)}
          >
            {!selectedPropertyId && (
              <option value="">Select property...</option>
            )}
            {properties.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Time Frame Toggle */}
        <div className="flex items-center bg-surface-100 rounded-lg p-0.5 text-xs font-medium">
          {TIME_FRAMES.map((tf, i) => (
            <button
              key={tf}
              className={cn(
                "px-2.5 py-1 rounded-md transition-colors",
                i === 0
                  ? "bg-white shadow-sm text-brand-700"
                  : "text-surface-500 hover:text-surface-700",
              )}
            >
              {tf}
            </button>
          ))}
        </div>

        {/* User */}
        {DEV_AUTH_BYPASS ? (
          <div className="w-8 h-8 bg-brand-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
            DV
          </div>
        ) : (
          <UserButton />
        )}
      </div>
    </nav>
  );
}
