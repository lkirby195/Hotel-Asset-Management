"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutGrid,
  TrendingUp,
  FileText,
  Home,
  Coffee,
  Sparkles,
  Flag,
  ShoppingBag,
  Mountain,
  MoreHorizontal,
  BookOpen,
  UserCog,
  RefreshCw,
  BarChart3,
  CalendarDays,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useProperty } from "@/providers/property-provider";
import { useRole } from "@/hooks/useRole";
import { PLATFORM_NAME, PLATFORM_ACCENT } from "@/lib/constants";
import type { LucideIcon } from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  disabled?: boolean;
}

interface NavGroup {
  label: string;
  items: NavItem[];
  badge?: string;
  requireRole?: "executive" | "admin";
}

const DEPT_ICONS: Record<string, LucideIcon> = {
  rooms: Home,
  fb: Coffee,
  spa: Sparkles,
  golf: Flag,
  retail: ShoppingBag,
  mountain: Mountain,
  other: MoreHorizontal,
};

const DEPT_LABELS: Record<string, string> = {
  rooms: "Rooms",
  fb: "F&B",
  spa: "Spa",
  golf: "Golf",
  retail: "Retail",
  mountain: "Mountain",
  other: "Other",
};

const ROLE_BADGE_COLORS: Record<string, string> = {
  admin: "bg-positive-100 text-positive-700",
  executive: "bg-brand-100 text-brand-700",
  operator: "bg-yellow-100 text-yellow-700",
  manager: "bg-surface-100 text-surface-600",
};

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function Sidebar() {
  const pathname = usePathname();
  const { properties, selectedPropertyId } = useProperty();
  const { role, isAdmin, isExecutive, user } = useRole();
  const selectedProperty = properties.find((p) => p.id === selectedPropertyId);

  const userName = user?.name || "Admin User";
  const userInitials = getInitials(userName);

  const departmentItems: NavItem[] = (selectedProperty?.departments ?? [])
    .filter((d) => d.is_active)
    .map((d) => ({
      label: DEPT_LABELS[d.type] ?? d.name,
      href: `/departments/${d.type}`,
      icon: DEPT_ICONS[d.type] ?? MoreHorizontal,
    }));

  const navGroups: NavGroup[] = [
    {
      label: "Overview",
      items: [
        { label: "Dashboard", href: "/dashboard", icon: LayoutGrid },
        { label: "Goals", href: "/goals", icon: LayoutGrid },
      ],
    },
    {
      label: "Reports",
      items: [
        { label: "Daily Report", href: "/daily-report", icon: CalendarDays },
        { label: "Performance", href: "/performance", icon: TrendingUp },
        { label: "P&L", href: "/pl", icon: FileText },
        { label: "Sales Performance", href: "/sales-performance", icon: BarChart3 },
      ],
    },
    ...(departmentItems.length > 0
      ? [{ label: "Departments", items: departmentItems } as NavGroup]
      : []),
    {
      label: "Executive",
      items: [{ label: "Portfolio", href: "/portfolio", icon: BookOpen }],
      requireRole: "executive" as const,
    },
    {
      label: "Admin",
      items: [
        { label: "Users", href: "/admin/users", icon: UserCog },
        { label: "Sync", href: "/admin/sync", icon: RefreshCw },
      ],
      requireRole: "admin" as const,
    },
  ];

  const visibleGroups = navGroups.filter((group) => {
    if (!group.requireRole) return true;
    if (group.requireRole === "admin") return isAdmin;
    if (group.requireRole === "executive") return isExecutive;
    return false;
  });

  return (
    <aside className="fixed left-0 top-0 h-screen w-[220px] bg-surface-900 flex flex-col shadow-lg z-40">
      {/* Logo */}
      <div className="flex h-14 items-center px-5">
        <span className="text-base font-bold text-white tracking-tight">
          {PLATFORM_NAME}{" "}
          <span className="text-brand-300 font-normal">{PLATFORM_ACCENT}</span>
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-5">
        {visibleGroups.map((group) => (
          <div key={group.label}>
            <div className="flex items-center gap-2 px-2 mb-1.5">
              <span className="text-[10px] font-medium uppercase tracking-wider text-surface-400">
                {group.label}
              </span>
              {group.badge && (
                <span className="text-[9px] bg-surface-700 text-surface-400 rounded-full px-1.5 py-0.5">
                  {group.badge}
                </span>
              )}
            </div>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                if (item.disabled) {
                  return (
                    <div
                      key={item.href}
                      className="flex items-center gap-3 rounded-md px-2 py-1.5 text-sm text-surface-500 opacity-50 cursor-not-allowed pointer-events-none"
                    >
                      <item.icon className="h-4 w-4 shrink-0 opacity-70" />
                      {item.label}
                    </div>
                  );
                }

                const isActive =
                  pathname === item.href ||
                  (item.href !== "/dashboard" &&
                    pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 px-2 py-1.5 text-sm transition-colors",
                      isActive
                        ? "bg-brand-900 text-brand-300 border-l-2 border-brand-300 rounded-none"
                        : "text-surface-300 hover:bg-surface-800 hover:text-white rounded-md"
                    )}
                  >
                    <item.icon
                      className={cn(
                        "h-4 w-4 shrink-0",
                        isActive ? "opacity-100" : "opacity-70"
                      )}
                    />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* User section at bottom */}
      <div className="border-t border-surface-700 px-3 py-3">
        <div className="flex items-center gap-2 px-2">
          <div className="h-7 w-7 rounded-full bg-brand-900 flex items-center justify-center">
            <span className="text-xs font-medium text-brand-300">{userInitials}</span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs text-surface-300 truncate">{userName}</div>
            <span
              className={cn(
                "text-[9px] font-medium rounded-full px-1.5 py-0.5 capitalize",
                ROLE_BADGE_COLORS[role] ?? ROLE_BADGE_COLORS.manager
              )}
            >
              {role}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
