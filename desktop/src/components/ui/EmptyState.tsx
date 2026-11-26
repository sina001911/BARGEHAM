import React from "react";

interface EmptyStateProps {
  icon: string;
  title: string;
  subtitle: string;
  actionText?: string;
  onAction?: () => void;
}

export default function EmptyState({ icon, title, subtitle, actionText, onAction }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-gray-500">
      <span className="text-6xl mb-4">{icon}</span>
      <h3 className="text-lg font-bold text-gray-900">{title}</h3>
      <p className="text-gray-600 max-w-md text-center">{subtitle}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="mt-6 px-6 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700 transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}
