"use client";

import { useState, useCallback } from "react";
import type { PeriodType } from "@/types/reports";

export function usePeriod(initial: PeriodType = "mtd") {
  const [period, setPeriod] = useState<PeriodType>(initial);
  const [customRange, setCustomRange] = useState<{
    start: string;
    end: string;
  } | null>(null);

  const changePeriod = useCallback((p: PeriodType) => {
    setPeriod(p);
    if (p !== "custom") setCustomRange(null);
  }, []);

  const setCustom = useCallback((start: string, end: string) => {
    setPeriod("custom");
    setCustomRange({ start, end });
  }, []);

  return { period, customRange, changePeriod, setCustom };
}
