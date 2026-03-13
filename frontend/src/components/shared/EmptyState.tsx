"use client";

interface EmptyStateProps {
  title?: string;
  message: string;
  icon?: React.ReactNode;
}

export function EmptyState({
  title,
  message,
  icon,
}: EmptyStateProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
      {icon && <div className="mx-auto mb-3 text-gray-300">{icon}</div>}
      {title && (
        <h3 className="text-sm font-medium text-gray-900 mb-1">{title}</h3>
      )}
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  );
}
