import React from "react";

export default function LoadingSpinner({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <div className={`${className} animate-spin rounded-full border-b-2 border-bargeham-600`} />
  );
}
