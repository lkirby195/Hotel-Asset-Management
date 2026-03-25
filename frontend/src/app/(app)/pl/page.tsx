"use client";

import { useState, useMemo, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import {
  ChevronLeft,
  ChevronRight,
  Download,
  FileText,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import { createApiClient } from "@/lib/api-client";
import { useProperty } from "@/providers/property-provider";
import { cn } from "@/lib/utils";
import type { ApiResponse } from "@/types/api";

/* ═══════════════════════════════════════════════════
   Types
   ═══════════════════════════════════════════════════ */

interface PLLineItem {
  id: string;
  code: string;
  name: string;
  parent_id: string | null;
  is_summary: boolean;
  data_type: string;
  sort_order: number;
  depth: number;
  actual: number;
  budget: number;
  variance_dollars: number;
  variance_pct: number | null;
  forecast_lock: number | null;
  prior_year_actual: number | null;
  py_variance_dollars: number | null;
  py_variance_pct: number | null;
}

interface PLReportData {
  property_id: string;
  property_name: string;
  period: string;
  start_date: string;
  end_date: string;
  lines: PLLineItem[];
  note: string | null;
}

interface MonthCloseInfo {
  year: number;
  month: number;
  is_closed: boolean;
  closed_at: string | null;
}

/* ═══════════════════════════════════════════════════
   Formatters
   ═══════════════════════════════════════════════════ */

const fullCurrFmt = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function fmtDollars(cents: number): string {
  const abs = Math.abs(cents) / 100;
  const s = fullCurrFmt.format(abs);
  return cents < 0 ? `(${s})` : s;
}

function fmtShort(cents: number): string {
  const dollars = Math.abs(cents) / 100;
  const neg = cents < 0;
  const wrap = (s: string) => (neg ? `(${s})` : s);
  if (dollars >= 1_000_000) return wrap(`$${(dollars / 1_000_000).toFixed(2)}M`);
  if (dollars >= 1_000) return wrap(`$${Math.round(dollars / 1_000)}K`);
  return wrap(`$${Math.round(dollars)}`);
}

function fmtVarDollars(cents: number): string {
  if (cents === 0) return "$0";
  return cents > 0 ? fmtDollars(cents) : `(${fmtDollars(Math.abs(cents))})`;
}

function fmtPct(d: number | null | undefined): string {
  if (d == null) return "—";
  const p = Math.abs(d * 100).toFixed(1);
  if (d > 0) return `+${p}%`;
  if (d < 0) return `-${p}%`;
  return `${p}%`;
}

function fmtMargin(cents: number, totalCents: number): string {
  if (totalCents === 0) return "—";
  return `${((cents / totalCents) * 100).toFixed(1)}%`;
}

/* ═══════════════════════════════════════════════════
   Row classification
   ═══════════════════════════════════════════════════ */

type RowStyle = "l0" | "l1" | "l2" | "total" | "subtotal";

const TOTAL_KW = [
  "total revenue",
  "gross operating profit",
  "net operating income",
  "ebitda",
];
const SUB_KW = [
  "dept profit",
  "department profit",
  "total undistributed",
  "total non-operating",
  "total other operated",
  "total fixed",
];

function classify(item: PLLineItem): RowStyle {
  const lc = item.name.toLowerCase();
  if (TOTAL_KW.some((k) => lc.includes(k))) return "total";
  if (SUB_KW.some((k) => lc.includes(k))) return "subtotal";
  if (lc.includes("capital reserve")) return "l1";
  if (item.depth === 0 && item.is_summary) return "l0";
  if (item.depth <= 1 && item.is_summary) return "l1";
  return "l2";
}

/* ═══════════════════════════════════════════════════
   Variance helpers
   ═══════════════════════════════════════════════════ */

function varColor(val: number, dt: string): string {
  if (val === 0) return "text-surface-500";
  const fav = dt === "expense" ? val < 0 : val > 0;
  return fav ? "text-positive-700" : "text-negative-700";
}

function badgeCls(val: number, dt: string): string {
  if (val === 0) return "text-surface-500 bg-surface-100";
  const fav = dt === "expense" ? val < 0 : val > 0;
  return fav ? "text-positive-700 bg-positive-50" : "text-negative-700 bg-negative-50";
}

/* ═══════════════════════════════════════════════════
   Visibility
   ═══════════════════════════════════════════════════ */

function visibleSet(
  lines: PLLineItem[],
  expanded: Set<string>,
): Set<string> {
  const parentOf = new Map<string, string | null>();
  for (const l of lines) parentOf.set(l.id, l.parent_id);

  const cache = new Map<string, boolean>();
  function ok(id: string): boolean {
    if (cache.has(id)) return cache.get(id)!;
    const pid = parentOf.get(id);
    if (pid == null) {
      cache.set(id, true);
      return true;
    }
    const vis = expanded.has(pid) && ok(pid);
    cache.set(id, vis);
    return vis;
  }

  const set = new Set<string>();
  for (const l of lines) if (ok(l.id)) set.add(l.id);
  return set;
}

/* ═══════════════════════════════════════════════════
   KPI extraction
   ═══════════════════════════════════════════════════ */

interface KPI {
  label: string;
  value: string;
  badge: string;
  favorable: boolean;
}

function extractKPIs(lines: PLLineItem[]): KPI[] {
  const find = (pat: string) =>
    lines.find((l) => l.name.toLowerCase().includes(pat));

  const moneyKpi = (label: string, item: PLLineItem | undefined): KPI => {
    if (!item) return { label, value: "—", badge: "", favorable: true };
    const sign = item.variance_dollars >= 0 ? "+" : "";
    return {
      label,
      value: fmtShort(item.actual),
      badge: `${sign}${fmtShort(item.variance_dollars)}`,
      favorable: item.variance_dollars >= 0,
    };
  };

  const pctKpi = (label: string, item: PLLineItem | undefined): KPI => {
    if (!item) return { label, value: "—", badge: "", favorable: true };
    return {
      label,
      value: fmtPct(item.actual / 10000) ?? "—",
      badge: fmtPct(item.variance_pct),
      favorable: (item.variance_dollars ?? 0) >= 0,
    };
  };

  const occ = find("occupancy");
  const adr = find("average daily rate") ?? lines.find((l) => l.name === "ADR");
  const revpar = find("revpar");

  return [
    occ
      ? {
          label: "Occupancy",
          value: `${(occ.actual / 100).toFixed(1)}%`,
          badge: `${occ.variance_dollars >= 0 ? "+" : ""}${(occ.variance_dollars / 100).toFixed(1)}pt vs Bgt`,
          favorable: occ.variance_dollars >= 0,
        }
      : { label: "Occupancy", value: "—", badge: "", favorable: true },
    adr
      ? {
          label: "ADR",
          value: fmtDollars(adr.actual),
          badge: fmtPct(adr.variance_pct),
          favorable: (adr.variance_dollars ?? 0) >= 0,
        }
      : { label: "ADR", value: "—", badge: "", favorable: true },
    revpar
      ? {
          label: "RevPAR",
          value: fmtDollars(revpar.actual),
          badge: fmtPct(revpar.variance_pct),
          favorable: (revpar.variance_dollars ?? 0) >= 0,
        }
      : { label: "RevPAR", value: "—", badge: "", favorable: true },
    moneyKpi("Total Rev", find("total revenue")),
    moneyKpi("GOP", find("gross operating profit")),
    moneyKpi("NOI", find("net operating income")),
    moneyKpi("EBITDA", find("ebitda")),
    { label: "STR RevPAR Idx", value: "—", badge: "", favorable: true },
  ];
}

/* ═══════════════════════════════════════════════════
   Flow / Flex
   ═══════════════════════════════════════════════════ */

interface FlowFlex {
  mode: "flow" | "flex";
  revVar: number;
  gopVar: number;
  ebitdaVar: number;
  gopPct: number;
  ebitdaPct: number;
  revVarStly: number;
  gopVarStly: number;
  ebitdaVarStly: number;
  gopPctStly: number;
  ebitdaPctStly: number;
}

function calcFlowFlex(lines: PLLineItem[]): FlowFlex | null {
  const find = (p: string) => lines.find((l) => l.name.toLowerCase().includes(p));
  const tr = find("total revenue");
  const gop = find("gross operating profit");
  const eb = find("ebitda");
  if (!tr || !gop || !eb) return null;

  const rv = tr.variance_dollars;
  const gv = gop.variance_dollars;
  const ev = eb.variance_dollars;
  const rvs = tr.py_variance_dollars ?? 0;
  const gvs = gop.py_variance_dollars ?? 0;
  const evs = eb.py_variance_dollars ?? 0;

  return {
    mode: rv >= 0 ? "flow" : "flex",
    revVar: rv,
    gopVar: gv,
    ebitdaVar: ev,
    gopPct: rv ? (gv / rv) * 100 : 0,
    ebitdaPct: rv ? (ev / rv) * 100 : 0,
    revVarStly: rvs,
    gopVarStly: gvs,
    ebitdaVarStly: evs,
    gopPctStly: rvs ? (gvs / rvs) * 100 : 0,
    ebitdaPctStly: rvs ? (evs / rvs) * 100 : 0,
  };
}

/* ═══════════════════════════════════════════════════
   Date helpers
   ═══════════════════════════════════════════════════ */

function monthName(m: number) {
  return new Date(2026, m - 1).toLocaleString("en-US", { month: "long" });
}
function monthShort(m: number) {
  return new Date(2026, m - 1).toLocaleString("en-US", { month: "short" });
}
function daysIn(y: number, m: number) {
  return new Date(y, m, 0).getDate();
}
function pad2(n: number) {
  return String(n).padStart(2, "0");
}

/* ═══════════════════════════════════════════════════
   Page Component
   ═══════════════════════════════════════════════════ */

export default function PLPage() {
  const { selectedPropertyId, properties } = useProperty();
  const { getToken } = useAuth();
  const api = createApiClient(getToken);

  const [year, setYear] = useState(2026);
  const [month, setMonth] = useState(2);
  const [view, setView] = useState<"summary" | "detail">("detail");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [childrenMap, setChildrenMap] = useState<Map<string, PLLineItem[]>>(new Map());
  const [loadingChildren, setLoadingChildren] = useState<Set<string>>(new Set());

  const property = properties.find((p) => p.id === selectedPropertyId);
  const start = `${year}-${pad2(month)}-01`;
  const end = `${year}-${pad2(month)}-${pad2(daysIn(year, month))}`;

  // ── Data fetching ────────────────────────────────
  const { data: report, isLoading } = useQuery<PLReportData>({
    queryKey: ["pl-report", selectedPropertyId, year, month],
    queryFn: async () => {
      const r = await api.get<ApiResponse<PLReportData>>(
        `/reports/inter-month/${selectedPropertyId}?period=custom&start=${start}&end=${end}`,
      );
      return r.data.data;
    },
    enabled: !!selectedPropertyId,
  });

  const { data: closes } = useQuery<MonthCloseInfo[]>({
    queryKey: ["month-close", selectedPropertyId],
    queryFn: async () => {
      const r = await api.get<ApiResponse<MonthCloseInfo[]>>(
        `/reports/month-close/${selectedPropertyId}`,
      );
      return r.data.data;
    },
    enabled: !!selectedPropertyId,
  });

  // ── Derived ──────────────────────────────────────
  const baseLines = report?.lines ?? [];

  // Merge base lines with loaded children, inserting children right after their parent
  const lines = useMemo(() => {
    if (childrenMap.size === 0) return baseLines;
    const result: PLLineItem[] = [];
    const insertedParents = new Set<string>();
    for (const line of baseLines) {
      result.push(line);
      // Recursively insert children (and their children) after each parent
      const insertChildren = (parentId: string) => {
        if (insertedParents.has(parentId)) return;
        insertedParents.add(parentId);
        const kids = childrenMap.get(parentId);
        if (!kids) return;
        for (const kid of kids) {
          result.push(kid);
          insertChildren(kid.id);
        }
      };
      insertChildren(line.id);
    }
    return result;
  }, [baseLines, childrenMap]);

  const vis = useMemo(() => visibleSet(lines, expanded), [lines, expanded]);
  const kpis = useMemo(() => extractKPIs(baseLines), [baseLines]);
  const ff = useMemo(() => calcFlowFlex(baseLines), [baseLines]);

  const isClosed =
    closes?.find((c) => c.year === year && c.month === month)?.is_closed ??
    false;

  const totalRev =
    lines.find((l) => l.name.toLowerCase().includes("total revenue"))?.actual ??
    0;

  // ── Navigation ───────────────────────────────────
  const prev = () => {
    setMonth((m) => (m === 1 ? (setYear((y) => y - 1), 12) : m - 1));
    setExpanded(new Set());
    setChildrenMap(new Map());
    setLoadingChildren(new Set());
  };
  const next = () => {
    setMonth((m) => (m === 12 ? (setYear((y) => y + 1), 1) : m + 1));
    setExpanded(new Set());
    setChildrenMap(new Map());
    setLoadingChildren(new Set());
  };
  const toggle = useCallback(
    async (id: string) => {
      // Collapsing — just toggle
      if (expanded.has(id)) {
        setExpanded((s) => {
          const n = new Set(s);
          n.delete(id);
          return n;
        });
        return;
      }

      // Expanding — fetch children if not already loaded
      if (!childrenMap.has(id)) {
        setLoadingChildren((s) => new Set(s).add(id));
        try {
          const r = await api.get<ApiResponse<PLLineItem[]>>(
            `/reports/inter-month/${selectedPropertyId}/children/${id}?period=custom&start=${start}&end=${end}`,
          );
          setChildrenMap((m) => {
            const next = new Map(m);
            next.set(id, r.data.data);
            return next;
          });
        } catch {
          // If fetch fails, still allow expand (will just show no children)
        } finally {
          setLoadingChildren((s) => {
            const n = new Set(s);
            n.delete(id);
            return n;
          });
        }
      }

      setExpanded((s) => {
        const n = new Set(s);
        n.add(id);
        return n;
      });
    },
    [expanded, childrenMap, api, selectedPropertyId, start, end],
  );

  // ── Guard ────────────────────────────────────────
  if (!selectedPropertyId) {
    return (
      <div className="max-w-[1500px] mx-auto px-6 py-6">
        <div className="rounded-xl border border-surface-200 bg-white p-8 text-center text-sm text-surface-500">
          Select a property to view P&L reports.
        </div>
      </div>
    );
  }

  const days = daysIn(year, month);
  const rooms = 224;
  const rna = rooms * days;
  const prevLabel = `${monthShort(month === 1 ? 12 : month - 1)} ${month === 1 ? year - 1 : year}`;
  const nextLabel = `${monthShort(month === 12 ? 1 : month + 1)} ${month === 12 ? year + 1 : year}`;

  /* ═══════════════════════════════════════════════════
     Render
     ═══════════════════════════════════════════════════ */
  return (
    <div className="max-w-[1500px] mx-auto px-6 py-6">
      {/* ── Close Banner ──────────────────────────── */}
      {!isClosed && (
        <div className="bg-warning-50 border border-warning-500/30 rounded-xl px-5 py-3 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-warning-500 shrink-0" />
            <div>
              <span className="text-sm font-semibold text-warning-700">
                {monthName(month)} {year} — Preliminary
              </span>
              <span className="text-xs text-warning-700/70 ml-2">
                Month-end close in progress
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ── Header ────────────────────────────────── */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-surface-900">
              Profit &amp; Loss Statement
            </h2>
            <div className="flex items-center bg-surface-100 rounded-lg p-0.5 text-xs font-medium">
              {(["summary", "detail"] as const).map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  className={cn(
                    "px-2.5 py-1 rounded-md capitalize transition-colors",
                    view === v
                      ? "bg-white shadow-sm text-brand-700"
                      : "text-surface-500",
                  )}
                >
                  {v}
                </button>
              ))}
            </div>
          </div>
          <p className="text-sm text-surface-500 mt-0.5">
            {property?.name ?? "Property"} — {monthName(month)} {year} |{" "}
            {rooms} Available Rooms | {days} Days |{" "}
            {rna.toLocaleString()} Room Nights Available
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={prev}
            className="flex items-center gap-1 px-3 py-1.5 text-sm border border-surface-200 rounded-lg hover:bg-surface-50"
          >
            <ChevronLeft className="w-3 h-3" /> {prevLabel}
          </button>
          <button
            onClick={next}
            className="flex items-center gap-1 px-3 py-1.5 text-sm border border-surface-200 rounded-lg hover:bg-surface-50"
          >
            {nextLabel} <ChevronRight className="w-3 h-3" />
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-surface-200 rounded-lg hover:bg-surface-50 ml-2">
            <FileText className="w-3.5 h-3.5" /> PDF
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-surface-200 rounded-lg hover:bg-surface-50">
            <Download className="w-3.5 h-3.5" /> Excel
          </button>
        </div>
      </div>

      {/* ── KPI Strip ─────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3 mb-6">
        {kpis.map((k) => (
          <div
            key={k.label}
            className="kpi-card bg-white rounded-lg border border-surface-200 p-3 text-center"
          >
            <div className="text-[10px] font-medium text-surface-400 uppercase tracking-wide">
              {k.label}
            </div>
            <div className="text-lg font-bold">{k.value}</div>
            {k.badge && (
              <span
                className={cn(
                  "inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium",
                  k.favorable
                    ? "text-positive-700 bg-positive-50"
                    : "text-negative-700 bg-negative-50",
                )}
              >
                {k.badge}
              </span>
            )}
          </div>
        ))}
      </div>

      {/* ── P&L Table ─────────────────────────────── */}
      {isLoading ? (
        <PLSkeleton />
      ) : lines.length === 0 ? (
        <div className="bg-white rounded-xl border border-surface-200 p-12 text-center text-sm text-surface-400">
          No data available for {monthName(month)} {year}.
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-surface-200 overflow-x-auto mb-6">
          <table className="w-full text-xs whitespace-nowrap tabular-nums">
            {/* Header */}
            <thead className="sticky top-0 z-40">
              <tr className="bg-surface-900 text-white">
                <th className="text-left py-3 px-4 font-semibold min-w-[220px]">
                  Line Item
                </th>
                <th className="text-right py-3 px-4 font-semibold">Actual</th>
                <th className="text-right py-3 px-4 font-semibold">Budget</th>
                <th className="text-right py-3 px-4 font-semibold">Fcst Lock</th>
                <th className="text-right py-3 px-4 font-semibold border-r-2 border-surface-300/40">
                  STLY
                </th>
                <th className="text-right py-3 px-4 font-semibold border-r-2 border-surface-300/40">
                  Margin
                </th>
                <th className="text-right py-3 px-4 font-semibold border-l-2 border-brand-500">
                  $ vs Bgt
                </th>
                <th className="text-right py-3 px-4 font-semibold">% vs Bgt</th>
                <th className="text-right py-3 px-4 font-semibold">$ vs Fcst</th>
                <th className="text-right py-3 px-4 font-semibold">
                  $ vs STLY
                </th>
                <th className="text-right py-3 px-4 font-semibold">
                  % vs STLY
                </th>
              </tr>
            </thead>

            <tbody>
              {lines
                .filter((l) => {
                  if (view === "summary") {
                    const s = classify(l);
                    return (
                      s === "l0" || s === "total" || s === "subtotal"
                    );
                  }
                  return vis.has(l.id);
                })
                .map((l) => (
                  <PLRow
                    key={l.id}
                    item={l}
                    totalRev={totalRev}
                    isExpanded={expanded.has(l.id)}
                    canExpand={l.is_summary && view === "detail"}
                    isLoadingChildren={loadingChildren.has(l.id)}
                    onToggle={() => toggle(l.id)}
                  />
                ))}

              {/* Flow / Flex */}
              {ff && <FlowFlexRows ff={ff} />}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Commentary ────────────────────────────── */}
      <div className="bg-white rounded-xl border border-surface-200 p-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-surface-700">
            Commentary — {monthName(month)} {year}
          </h3>
          <button className="text-xs text-brand-600 font-medium hover:text-brand-800">
            + Add Comment
          </button>
        </div>
        <div className="space-y-3">
          <Comment
            tags={[
              { label: "Market Conditions", cls: "bg-amber-100 text-amber-800" },
              { label: "Rooms", cls: "bg-blue-100 text-blue-800" },
            ]}
            author="Jason M."
            date={`${monthShort(month)} ${days}`}
            text="Presidents' Day weekend drove strong transient demand. ADR pushed above $310 for 3 consecutive nights. Group block exceeded pickup expectations by 12%."
          />
          <Comment
            tags={[
              { label: "Staffing", cls: "bg-red-100 text-red-800" },
              { label: "F&B", cls: "bg-purple-100 text-purple-800" },
            ]}
            author="Jason M."
            date={`${monthShort(month)} ${days}`}
            text="Restaurant covers below budget due to 2 server vacancies. Food cost elevated — new line cook training, expect normalization next month. Bar revenue strong on apres-ski traffic."
          />
          <Comment
            tags={[
              { label: "One-Time Event", cls: "bg-green-100 text-green-800" },
              { label: "Mountain Ops", cls: "bg-cyan-100 text-cyan-800" },
            ]}
            author="Jason M."
            date={`${monthShort(month)} ${days}`}
            text="Exceptional snow conditions drove strong YoY increase in mountain ops revenue. Extended season operations approved through April 6 based on snowpack levels."
          />
        </div>
      </div>

      {/* ── Footer ────────────────────────────────── */}
      <div className="text-center text-xs text-surface-400 pb-4">
        {monthName(month)} {year} —{" "}
        {isClosed ? "Closed" : "Preliminary (close pending)"} | Data synced via
        ProfitSword
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   PLRow sub-component
   ═══════════════════════════════════════════════════ */

function PLRow({
  item,
  totalRev,
  isExpanded,
  canExpand,
  isLoadingChildren,
  onToggle,
}: {
  item: PLLineItem;
  totalRev: number;
  isExpanded: boolean;
  canExpand: boolean;
  isLoadingChildren: boolean;
  onToggle: () => void;
}) {
  const s = classify(item);
  const isEbitda = item.name.toLowerCase().includes("ebitda");
  const indent = item.depth * 24 + 16;
  const fcstVar =
    item.forecast_lock != null ? item.actual - item.forecast_lock : null;

  // L0 rows show no numbers (just the header bar)
  const showNums = s !== "l0";

  // Total rows use light colored text for favorable
  const isTotalRow = s === "total";
  const totalVarStyle = (v: number) =>
    isTotalRow ? { color: v >= 0 ? "#a7f3d0" : "#fca5a5" } : undefined;
  const totalBadgeStyle = (v: number) =>
    isTotalRow
      ? { color: v >= 0 ? "#a7f3d0" : "#fca5a5", background: "rgba(255,255,255,0.1)" }
      : undefined;

  return (
    <tr
      className={cn(
        s === "l0" &&
          "bg-surface-800 text-white font-bold cursor-pointer hover:bg-surface-700",
        s === "l1" &&
          "bg-surface-100 font-semibold cursor-pointer hover:bg-surface-200",
        s === "l2" && "hover:bg-surface-50",
        s === "total" && !isEbitda && "bg-surface-900 text-white font-bold",
        s === "subtotal" && "bg-surface-200 font-bold",
      )}
      style={isEbitda && s === "total" ? { background: "#0c4a6e", color: "#fff", fontWeight: 700 } : undefined}
      onClick={canExpand ? onToggle : undefined}
    >
      {/* Line Item */}
      <td className="py-2 px-4" style={{ paddingLeft: indent }}>
        {canExpand && (
          isLoadingChildren ? (
            <Loader2 className="inline-block mr-1.5 w-3 h-3 animate-spin" />
          ) : (
            <span
              className={cn(
                "inline-block mr-1.5 text-[10px] transition-transform duration-150",
                isExpanded && "rotate-90",
              )}
            >
              &#9654;
            </span>
          )
        )}
        {item.name}
      </td>

      {/* Actual */}
      <td className={cn("py-2 px-4 text-right", isTotalRow && "text-sm")}>
        {showNums ? fmtDollars(item.actual) : ""}
      </td>

      {/* Budget */}
      <td
        className={cn(
          "py-2 px-4 text-right",
          s === "l2" && "text-surface-500",
          isTotalRow && "text-sm",
        )}
      >
        {showNums ? fmtDollars(item.budget) : ""}
      </td>

      {/* Fcst Lock */}
      <td
        className={cn(
          "py-2 px-4 text-right",
          s === "l2" && "text-surface-500",
          isTotalRow && "text-sm",
        )}
      >
        {showNums
          ? item.forecast_lock != null
            ? fmtDollars(item.forecast_lock)
            : "—"
          : ""}
      </td>

      {/* STLY */}
      <td
        className={cn(
          "py-2 px-4 text-right border-r-2 border-surface-300",
          s === "l2" && "text-surface-500",
          isTotalRow && "text-sm",
        )}
      >
        {showNums
          ? item.prior_year_actual != null
            ? fmtDollars(item.prior_year_actual)
            : "—"
          : ""}
      </td>

      {/* Margin */}
      <td className="py-2 px-4 text-right border-r-2 border-surface-300">
        {showNums
          ? item.data_type === "revenue"
            ? "—"
            : fmtMargin(item.actual, totalRev)
          : ""}
      </td>

      {/* $ vs Bgt */}
      <td
        className={cn(
          "py-2 px-4 text-right border-l-2 border-brand-500",
          !isTotalRow && varColor(item.variance_dollars, item.data_type),
          isTotalRow && "text-sm",
        )}
        style={isTotalRow ? totalVarStyle(item.variance_dollars) : undefined}
      >
        {showNums ? fmtVarDollars(item.variance_dollars) : ""}
      </td>

      {/* % vs Bgt */}
      <td className="py-2 px-4 text-right">
        {showNums ? (
          <span
            className={cn(
              "inline-flex px-1 py-0.5 rounded text-[10px] font-medium",
              !isTotalRow && badgeCls(item.variance_dollars, item.data_type),
            )}
            style={isTotalRow ? totalBadgeStyle(item.variance_dollars) : undefined}
          >
            {fmtPct(item.variance_pct)}
          </span>
        ) : (
          ""
        )}
      </td>

      {/* $ vs Fcst */}
      <td
        className={cn(
          "py-2 px-4 text-right",
          !isTotalRow &&
            (fcstVar != null
              ? varColor(fcstVar, item.data_type)
              : "text-surface-400"),
          isTotalRow && "text-sm",
        )}
        style={isTotalRow && fcstVar != null ? totalVarStyle(fcstVar) : undefined}
      >
        {showNums ? (fcstVar != null ? fmtVarDollars(fcstVar) : "—") : ""}
      </td>

      {/* $ vs STLY */}
      <td
        className={cn(
          "py-2 px-4 text-right",
          !isTotalRow && varColor(item.py_variance_dollars ?? 0, item.data_type),
          isTotalRow && "text-sm",
        )}
        style={
          isTotalRow
            ? totalVarStyle(item.py_variance_dollars ?? 0)
            : undefined
        }
      >
        {showNums
          ? item.py_variance_dollars != null
            ? fmtVarDollars(item.py_variance_dollars)
            : "—"
          : ""}
      </td>

      {/* % vs STLY */}
      <td className="py-2 px-4 text-right">
        {showNums ? (
          <span
            className={cn(
              "inline-flex px-1 py-0.5 rounded text-[10px] font-medium",
              !isTotalRow &&
                badgeCls(item.py_variance_dollars ?? 0, item.data_type),
            )}
            style={
              isTotalRow
                ? totalBadgeStyle(item.py_variance_dollars ?? 0)
                : undefined
            }
          >
            {fmtPct(item.py_variance_pct)}
          </span>
        ) : (
          ""
        )}
      </td>
    </tr>
  );
}

/* ═══════════════════════════════════════════════════
   Flow / Flex rows
   ═══════════════════════════════════════════════════ */

function FlowFlexRows({ ff }: { ff: FlowFlex }) {
  const isFlow = ff.mode === "flow";
  const bg = isFlow ? "bg-flow-50" : "bg-flex-50";
  const textCls = isFlow ? "text-flow-700" : "text-flex-700";
  const badgeCls2 = isFlow
    ? "text-flow-700 bg-flow-100"
    : "text-flex-700 bg-flex-100";
  const label = isFlow ? "Flow" : "Flex";

  const row = (
    vs: string,
    revV: number,
    gopV: number,
    ebV: number,
    gopP: number,
    ebP: number,
  ) => (
    <tr className={bg}>
      <td className={cn("py-3 px-4 font-bold", textCls)}>
        {label}-Through vs {vs}
      </td>
      <td className="py-3 px-4 text-right" colSpan={4}>
        <span className="text-xs text-surface-500">
          Revenue {fmtVarDollars(revV)} | GOP {fmtVarDollars(gopV)} | EBITDA{" "}
          {fmtVarDollars(ebV)}
        </span>
      </td>
      <td className="py-3 px-4 border-r-2 border-surface-300" />
      <td className="py-3 px-4 text-right border-l-2 border-brand-500">
        <span className={cn("inline-flex px-2 py-1 rounded text-xs font-bold", badgeCls2)}>
          GOP: {gopP.toFixed(1)}%
        </span>
      </td>
      <td className="py-3 px-4 text-right">
        <span className={cn("inline-flex px-2 py-1 rounded text-xs font-bold", badgeCls2)}>
          EBITDA: {ebP.toFixed(1)}%
        </span>
      </td>
      <td className="py-3 px-4" colSpan={3} />
    </tr>
  );

  return (
    <>
      {row("Budget", ff.revVar, ff.gopVar, ff.ebitdaVar, ff.gopPct, ff.ebitdaPct)}
      {row(
        "STLY",
        ff.revVarStly,
        ff.gopVarStly,
        ff.ebitdaVarStly,
        ff.gopPctStly,
        ff.ebitdaPctStly,
      )}
    </>
  );
}

/* ═══════════════════════════════════════════════════
   Commentary
   ═══════════════════════════════════════════════════ */

function Comment({
  tags,
  author,
  date,
  text,
}: {
  tags: { label: string; cls: string }[];
  author: string;
  date: string;
  text: string;
}) {
  return (
    <div className="border-l-[3px] border-brand-500 bg-surface-50 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        {tags.map((t) => (
          <span
            key={t.label}
            className={cn(
              "inline-flex px-2 py-0.5 rounded text-[10px] font-medium",
              t.cls,
            )}
          >
            {t.label}
          </span>
        ))}
        <span className="text-xs text-surface-400 ml-auto">
          {author} | {date}
        </span>
      </div>
      <p className="text-sm text-surface-700">{text}</p>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   Loading skeleton
   ═══════════════════════════════════════════════════ */

function PLSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-surface-200 p-6 mb-6 space-y-3">
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} className="h-8 bg-surface-100 rounded animate-pulse" />
      ))}
    </div>
  );
}
