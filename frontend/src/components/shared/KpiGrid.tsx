"use client";

import { KpiCard, type KpiCardProps } from "./KpiCard";

interface KpiGridProps {
  cards: KpiCardProps[];
}

export function KpiGrid({ cards }: KpiGridProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {cards.map((card) => (
        <KpiCard key={card.label} {...card} />
      ))}
    </div>
  );
}
