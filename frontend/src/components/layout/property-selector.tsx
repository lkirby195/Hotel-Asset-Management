"use client";

import { useProperty } from "@/providers/property-provider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function PropertySelector() {
  const { properties, selectedPropertyId, setSelectedPropertyId, isLoading } =
    useProperty();

  return (
    <Select
      value={selectedPropertyId ?? ""}
      onValueChange={(v) => v && setSelectedPropertyId(v)}
      disabled={isLoading}
    >
      <SelectTrigger className="w-64">
        <SelectValue placeholder="Select a property..." />
      </SelectTrigger>
      <SelectContent>
        {properties.map((p) => (
          <SelectItem key={p.id} value={p.id}>
            {p.name} ({p.code})
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
