import React, { useEffect, useState } from "react";
import { useStore } from "@/store/useStore";
import { CheckCircle, AlertCircle, Info } from "lucide-react";

export default function Toast() {
  const [toasts, setToasts] = useState<Array<{ id: number; title: string; type: "success" | "error" | "info" }>>([]);

  useEffect(() => {
    const unsubscribe = useStore.subscribe(
      (state) => state,
      () => {
        // We'll use a separate notification system
      }
    );
    return () => unsubscribe();
  }, []);

  const addToast = (title: string, type: "success" | "error" | "info" = "info") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, title, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  const removeToast = (id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const iconMap = {
    success: <CheckCircle className="w-5 h-5 text-green-500" />,
    error: <AlertCircle className="w-5 h-5 text-red-500" />,
    info: <Info className="w-5 h-5 text-blue-500" />,
  };

  const bgMap = {
    success: "bg-green-50 border-green-200",
    error: "bg-red-50 border-red-200",
    info: "bg-blue-50 border-blue-200",
  };

  const textMap = {
    success: "text-green-700",
    error: "text-red-700",
    info: "text-blue-700",
  };

  return (
    <div className="fixed top-5 right-5 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`pointer-events-auto flex items-start gap-3 p-4 rounded-lg shadow-lg border ${bgMap[t.type]} animate-in fade-in slide-in-from-right-4 duration-300`}
        >
          <div className="flex-shrink-0 mt-0.5">{iconMap[t.type]}</div>
          <div className="text-sm font-medium {textMap[t.type]}">{t.title}</div>
          <button
            onClick={() => removeToast(t.id)}
            className="ml-auto mt-1 opacity-50 hover:opacity-100"
          >
            <span className="sr-only">بستن</span>
            <span className="block h-6 w-6 rounded-full hover:bg-gray-200 flex items-center justify-center">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </span>
          </button>
        </div>
      ))}
    </div>
  );
}
