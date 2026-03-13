"use client";

import { UserButton } from "@clerk/nextjs";
import { PropertySelector } from "./property-selector";

const DEV_AUTH_BYPASS = process.env.NEXT_PUBLIC_DEV_AUTH_BYPASS === "true";

export function Header() {
  return (
    <header className="flex h-14 items-center justify-between border-b bg-white px-6">
      <PropertySelector />
      {DEV_AUTH_BYPASS ? (
        <span className="text-xs text-gray-400">Dev Mode</span>
      ) : (
        <UserButton />
      )}
    </header>
  );
}
