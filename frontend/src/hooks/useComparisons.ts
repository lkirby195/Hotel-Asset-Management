"use client";

import { useState, useCallback, useEffect } from "react";
import { DEFAULT_COMPARISONS } from "@/lib/constants";
import type { ComparisonType } from "@/types/reports";

const STORAGE_KEY = "hotel-am-comparisons";

function loadFromStorage(): ComparisonType[] {
  if (typeof window === "undefined") return DEFAULT_COMPARISONS;
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored) as ComparisonType[];
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch {
    // ignore parse errors
  }
  return DEFAULT_COMPARISONS;
}

export function useComparisons() {
  const [activeComparisons, setActiveComparisons] = useState<Set<ComparisonType>>(
    () => new Set(loadFromStorage())
  );

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...activeComparisons]));
  }, [activeComparisons]);

  const toggleComparison = useCallback((type: ComparisonType) => {
    setActiveComparisons((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        // Prevent deselecting the last one
        if (next.size <= 1) return prev;
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  }, []);

  const isActive = useCallback(
    (type: ComparisonType) => activeComparisons.has(type),
    [activeComparisons]
  );

  return { activeComparisons, toggleComparison, isActive };
}
