"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { useProperties } from "@/hooks/use-properties";
import type { Property } from "@/lib/types";

interface PropertyContextValue {
  selectedPropertyId: string | null;
  setSelectedPropertyId: (id: string) => void;
  properties: Property[];
  isLoading: boolean;
}

const PropertyContext = createContext<PropertyContextValue>({
  selectedPropertyId: null,
  setSelectedPropertyId: () => {},
  properties: [],
  isLoading: true,
});

export function PropertyProvider({ children }: { children: ReactNode }) {
  const { data: properties = [], isLoading } = useProperties();
  const [selectedPropertyId, setSelectedPropertyId] = useState<string | null>(
    null
  );

  // Auto-select first property when list loads
  useEffect(() => {
    if (properties.length > 0 && !selectedPropertyId) {
      setSelectedPropertyId(properties[0].id);
    }
  }, [properties, selectedPropertyId]);

  return (
    <PropertyContext.Provider
      value={{ selectedPropertyId, setSelectedPropertyId, properties, isLoading }}
    >
      {children}
    </PropertyContext.Provider>
  );
}

export const useProperty = () => useContext(PropertyContext);
