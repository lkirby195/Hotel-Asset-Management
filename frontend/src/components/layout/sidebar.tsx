"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutGrid,
  TrendingUp,
  Clock,
  FileText,
  Users,
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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useProperty } from "@/providers/property-provider";
import type { LucideIcon } from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

interface NavGroup {
  label: string;
  items: NavItem[];
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

export function Sidebar() {
  const pathname = usePathname();
  const { properties, selectedPropertyId } = useProperty();
  const selectedProperty = properties.find((p) => p.id === selectedPropertyId);

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
        { label: "Goals", href: "/dashboard", icon: LayoutGrid },
        { label: "Inter-month", href: "/inter-month", icon: TrendingUp },
        { label: "Pace", href: "/pace", icon: Clock },
      ],
    },
    {
      label: "Reports",
      items: [
        { label: "Month-end", href: "/month-end", icon: FileText },
        { label: "Sales", href: "/sales", icon: Users },
      ],
    },
    ...(departmentItems.length > 0
      ? [{ label: "Departments", items: departmentItems }]
      : []),
    {
      label: "Executive",
      items: [{ label: "Portfolio", href: "/executive", icon: BookOpen }],
    },
    {
      label: "Admin",
      items: [
        { label: "Users", href: "/admin/users", icon: UserCog },
        { label: "Sync", href: "/admin/sync", icon: RefreshCw },
      ],
    },
  ];

  return (
    <aside className="fixed left-0 top-0 h-screen w-[220px] bg-sidebar-bg flex flex-col shadow-lg z-40">
      {/* Logo */}
      <div className="flex h-14 items-center px-5">
        <span className="text-base font-bold text-gray-50 tracking-tight">
          APEX{" "}
          <span className="text-sidebar-accent font-normal">hospitality</span>
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-5">
        {navGroups.map((group) => (
          <div key={group.label}>
            <div className="text-[10px] font-medium uppercase tracking-wider text-sidebar-group px-2 mb-1.5">
              {group.label}
            </div>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/dashboard" &&
                    pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 rounded-md px-2 py-1.5 text-sm transition-colors",
                      isActive
                        ? "bg-sidebar-active text-sidebar-accent border-r-2 border-sidebar-accent"
                        : "text-sidebar-text hover:bg-sidebar-hover hover:text-gray-300"
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
      <div className="border-t border-gray-800 px-3 py-3">
        <div className="flex items-center gap-2 px-2">
          <div className="h-7 w-7 rounded-full bg-sidebar-active flex items-center justify-center">
            <span className="text-xs font-medium text-sidebar-accent">LK</span>
          </div>
          <div className="text-xs text-sidebar-text truncate">Logan Kirby</div>
        </div>
      </div>
    </aside>
  );
}
