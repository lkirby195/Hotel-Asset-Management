"use client";

interface SectionHeaderProps {
  title: string;
}

export function SectionHeader({ title }: SectionHeaderProps) {
  return (
    <div className="pt-6 pb-2">
      <h3 className="text-sm font-medium text-gray-900 border-b-2 border-brand inline-block pb-1">
        {title}
      </h3>
    </div>
  );
}
