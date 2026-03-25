"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { ChevronLeft, ChevronRight, Download, Loader2 } from "lucide-react";
import { createApiClient } from "@/lib/api-client";
import { useProperty } from "@/providers/property-provider";
import { cn } from "@/lib/utils";
import { DualPanelTable } from "@/components/daily-report/DualPanelTable";
import type { ApiResponse } from "@/types/api";
import type { DailyReportResponse } from "@/types/daily-report";

/* ── Helpers ──────────────────────────────────────── */

const TAB_KEYS = [
  "Room Performance",
  "Ancillary Revenue",
  "Labor",
  "STR Competitive",
] as const;

function pad2(n: number) {
  return String(n).padStart(2, "0");
}

function fmtDate(d: Date): string {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

function fmtDisplay(d: Date): string {
  return d.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function fmtShortDate(d: Date): string {
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function daysInMonth(y: number, m: number) {
  return new Date(y, m + 1, 0).getDate();
}

/* ── Page Component ───────────────────────────────── */

export default function DailyReportPage() {
  const { selectedPropertyId, properties } = useProperty();
  const { getToken } = useAuth();
  const api = createApiClient(getToken);

  const [date, setDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 1); // default to yesterday
    return d;
  });
  const [activeTab, setActiveTab] = useState<string>(TAB_KEYS[0]);

  const property = properties.find((p) => p.id === selectedPropertyId);
  const dateStr = fmtDate(date);

  const { data: report, isLoading } = useQuery<DailyReportResponse>({
    queryKey: ["daily-report", selectedPropertyId, dateStr],
    queryFn: async () => {
      const r = await api.get<ApiResponse<DailyReportResponse>>(
        `/daily-report/${selectedPropertyId}?date=${dateStr}`,
      );
      return r.data.data;
    },
    enabled: !!selectedPropertyId,
  });

  // Navigation
  const prevDay = () => {
    setDate((d) => {
      const n = new Date(d);
      n.setDate(n.getDate() - 1);
      return n;
    });
  };
  const nextDay = () => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    setDate((d) => {
      const n = new Date(d);
      n.setDate(n.getDate() + 1);
      return n >= today ? d : n;
    });
  };

  const isToday = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const comp = new Date(date);
    comp.setHours(0, 0, 0, 0);
    return comp >= today;
  }, [date]);

  // MTD range info
  const mtdRange = useMemo(() => {
    const m = date.getMonth();
    const y = date.getFullYear();
    const start = new Date(y, m, 1);
    const dayNum = date.getDate();
    const totalDays = daysInMonth(y, m);
    const pct = ((dayNum / totalDays) * 100).toFixed(1);
    return {
      label: `${fmtShortDate(start)}–${fmtShortDate(date)}, ${y}`,
      progress: `${dayNum} of ${totalDays} days (${pct}%)`,
    };
  }, [date]);

  // Sections for the active tab
  const sections = useMemo(() => {
    if (!report?.sections) return [];
    return report.sections[activeTab] ?? [];
  }, [report, activeTab]);

  // Available tabs (only show tabs that have data, fall back to all)
  const availableTabs = useMemo(() => {
    if (!report?.sections) return TAB_KEYS;
    return TAB_KEYS.filter(
      (k) => report.sections[k] && report.sections[k].length > 0,
    );
  }, [report]);

  /* ── Guard ──────────────────────────────────────── */
  if (!selectedPropertyId) {
    return (
      <div className="max-w-[1400px] mx-auto px-6 py-6">
        <div className="rounded-xl border border-surface-200 bg-white p-8 text-center text-sm text-surface-500">
          Select a property to view the daily report.
        </div>
      </div>
    );
  }

  const prevDate = new Date(date);
  prevDate.setDate(prevDate.getDate() - 1);
  const nextDate = new Date(date);
  nextDate.setDate(nextDate.getDate() + 1);

  /* ── Render ─────────────────────────────────────── */
  return (
    <div className="max-w-[1400px] mx-auto px-6 py-6">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-surface-900">
            Daily Performance Report
          </h2>
          <p className="text-sm text-surface-500 mt-0.5">
            {property?.name ?? "Property"} — {fmtDisplay(date)}
            {report?.available_rooms
              ? ` · ${report.available_rooms} Available Rooms`
              : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={prevDay}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-surface-200 rounded-lg hover:bg-surface-50"
          >
            <ChevronLeft className="w-3 h-3" />
            {fmtShortDate(prevDate)}
          </button>
          <button
            onClick={nextDay}
            disabled={isToday}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 text-sm border border-surface-200 rounded-lg",
              isToday
                ? "opacity-50 cursor-not-allowed"
                : "hover:bg-surface-50",
            )}
          >
            {fmtShortDate(nextDate)}
            <ChevronRight className="w-3 h-3" />
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-surface-200 rounded-lg hover:bg-surface-50 ml-2">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-6 border-b border-surface-200 mb-6">
        {TAB_KEYS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "pb-3 text-sm transition-colors",
              activeTab === tab
                ? "border-b-2 border-brand-500 text-brand-700 font-semibold"
                : "border-b-2 border-transparent text-surface-500 hover:text-surface-700",
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="w-6 h-6 animate-spin text-brand-500" />
          <span className="ml-2 text-sm text-surface-500">
            Loading report...
          </span>
        </div>
      ) : sections.length === 0 ? (
        <div className="bg-white rounded-xl border border-surface-200 p-12 text-center text-sm text-surface-400">
          No data available for {fmtDisplay(date)}.
          {!availableTabs.includes(activeTab as (typeof TAB_KEYS)[number]) &&
            availableTabs.length > 0 && (
              <span className="block mt-2">
                Try the{" "}
                <button
                  onClick={() => setActiveTab(availableTabs[0])}
                  className="text-brand-600 underline"
                >
                  {availableTabs[0]}
                </button>{" "}
                tab.
              </span>
            )}
        </div>
      ) : (
        <DualPanelTable
          sections={sections}
          reportDate={fmtDisplay(date)}
          mtdRange={mtdRange.label}
          mtdProgress={mtdRange.progress}
        />
      )}

      {/* Footer */}
      <div className="text-center text-xs text-surface-400 pb-4 mt-6">
        Daily Report — {fmtDisplay(date)} | Data synced via ProfitSword
      </div>
    </div>
  );
}
