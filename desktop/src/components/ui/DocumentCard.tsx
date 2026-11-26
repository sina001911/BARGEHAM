import React from "react";
import { useStore } from "@/store/useStore";
import { api, notify } from "@/lib/api";
import { FileText, Download, Trash2, Edit3 } from "lucide-react";

interface DocumentCardProps {
  doc: any;
  onDelete?: () => void;
}

const statusStyles: Record<string, string> = {
  ready: "bg-green-100 text-green-700",
  processing: "bg-yellow-100 text-yellow-700 animate-pulse",
  ocr_failed: "bg-red-100 text-red-700",
  error: "bg-red-100 text-red-700",
  uploading: "bg-blue-100 text-blue-700",
  duplicate: "bg-purple-100 text-purple-700",
};

export default function DocumentCard({ doc, onDelete }: DocumentCardProps) {
  const { removeDocument } = useStore();

  const handleDownload = async () => {
    try {
      const blobUrl = await api.downloadDocument(doc.id);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = doc.file_name || "document";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(blobUrl), 100);
    } catch (err: any) {
      notify.error("خطا در دانلود", err.message);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("آیا مطمئنید که می‌خواهید این سند را حذف کنید؟")) return;
    try {
      await api.deleteDocument(doc.id);
      removeDocument(doc.id);
      onDelete?.();
      notify.success("حذف شد", "سند با موفقیت حذف شد");
    } catch (err: any) {
      notify.error("خطا", err.message);
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:border-bargeham-200 transition-colors flex items-start gap-3">
      <div className="flex-shrink-0 mt-0.5">
        <FileText className="w-6 h-6 text-gray-400" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-medium text-gray-900 truncate max-w-[200px]">
            {doc.title || doc.file_name}
          </h3>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusStyles[doc.status] || "bg-gray-100 text-gray-600"}`}>
            {doc.status}
          </span>
        </div>
        <p className="text-sm text-gray-600 truncate">{doc.file_name}</p>
        <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
          <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
          <span>•</span>
          <span>{doc.language || "—"}</span>
          {doc.page_count && <span>• {doc.page_count} صفحه</span>}
        </div>
      </div>
      <div className="flex items-center gap-2 ml-2">
        <button
          onClick={handleDownload}
          className="p-2 text-gray-400 hover:text-bargeham-600 rounded hover:bg-gray-100"
          title="دانلود"
        >
          <Download className="w-4 h-4" />
        </button>
        <button
          onClick={() => {
            window.location.hash = `#documents/${doc.id}`;
          }}
          className="p-2 text-gray-400 hover:text-blue-600 rounded hover:bg-gray-100"
          title="مشاهده"
        >
          <FileText className="w-4 h-4" />
        </button>
        <button
          onClick={handleDelete}
          className="p-2 text-gray-400 hover:text-red-600 rounded hover:bg-red-50"
          title="حذف"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
