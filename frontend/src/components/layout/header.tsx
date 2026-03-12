"use client";

import { UserButton } from "@clerk/nextjs";
import { PropertySelector } from "./property-selector";

export function Header() {
  return (
    <header className="flex h-14 items-center justify-between border-b bg-white px-6">
      <PropertySelector />
      <UserButton />
    </header>
  );
}
