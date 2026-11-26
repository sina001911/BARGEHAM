import React, { useEffect, useState } from "react";
import { useStore } from "@/store/useStore";
import { api, notify, openExternal } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import EmptyState from "@/components/ui/EmptyState";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { Download, ArrowLeft, Copy } from "lucide-react";

interface DocumentDetailPageProps {
  documentId: string;
}

export default function DocumentDetailPage({ documentId }: DocumentDetailPageProps) {
  const { currentDoc, loading, error, fetchDocument } = useStore();
  const [activeTab, setActiveTab] = useState<"metadata" | "chunks">("metadata");

  useEffect(() => {
    if (documentId) {
      fetchDocument(documentId);
    }
  }, [documentId, fetchDocument]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center text-red-600">
        {error}
      </div>
    );
  }

  const doc = currentDoc;
  if (!doc) {
    return (
      <EmptyState
        icon="📄"
        title="سند یافت نشد"
        subtitle="سندی با این شناسه یافت نشد."
        actionText="بازگشت به اسناد"
        onAction={() => {
          window.location.hash = "#documents";
        }}
      />
    );
  }

  const chunks = doc.chunks || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={() => {
            window.location.hash = "#documents";
          }}
          className="flex items-center gap-2 text-sm text-bargeham-600 hover:text-bargeham-700"
        >
          <ArrowLeft className="w-4 h-4" />
          بازگشت به اسناد
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={async () => {
              try {
                const blobUrl = await api.downloadDocument(documentId);
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
            }}
            className="px-4 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700 flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            دانلود فایل
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Metadata Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="font-bold text-gray-900 mb-4">اطلاعات سند</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">عنوان:</span>
              <span className="font-medium text-gray-900 truncate max-w-[200px]">
                {doc.title || doc.file_name}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">نام فایل:</span>
              <span className="font-mono text-sm text-gray-700 truncate max-w-[200px]">
                {doc.file_name}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">نوع سند:</span>
              <Badge variant="default">{doc.document_type}</Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">حالت:</span>
              <Badge
                variant={
                  doc.status === "ready"
                    ? "success"
                    : doc.status === "processing"
                    ? "warning"
                    : doc.status === "duplicate"
                    ? "info"
                    : "error"
                }
              >
                {doc.status}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">حجم:</span>
              <span className="font-mono text-sm text-gray-700">
                {(doc.file_size / 1024).toFixed(1)} KB
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">صفحات:</span>
              <span className="font-mono text-sm text-gray-700">
                {doc.page_count ?? "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">زبان:</span>
              <span className="font-mono text-sm text-gray-700">{doc.language ?? "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">امکان شبکه متنی:</span>
              <span className={`font-mono text-sm ${doc.has_text_layer ? "text-green-600" : "text-gray-600"}`}>
                {doc.has_text_layer ? "بله" : "خیر"}
              </span>
            </div>
            {doc.ocr_confidence !== null && doc.ocr_confidence !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-600">اعتماد OCR:</span>
                <span className="font-mono text-sm text-gray-700">
                  {(doc.ocr_confidence * 100).toFixed(1)}%
                </span>
              </div>
            )}
            {doc.classification && (
              <div className="flex justify-between">
                <span className="text-gray-600">دسته‌بندی:</span>
                <Badge variant="info">{doc.classification}</Badge>
                <span className="text-xs text-gray-500">
                  ({(doc.classification_confidence ?? 0) * 100}%)
                </span>
              </div>
            )}
            {doc.duplicate_of && (
              <div className="flex justify-between">
                <span className="text-gray-600">تکرار نزدیک:</span>
                <Badge variant="warning">تکراری</Badge>
              </div>
            )}
          </div>
        </div>

        {/* Tabs Content */}
        <div className="md:col-span-2 bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col h-full">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab("metadata")}
              className={`px-6 py-3 text-sm font-medium border-b-2 ${
                activeTab === "metadata"
                  ? "border-bargeham-600 text-bargeham-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              متادیتا
            </button>
            <button
              onClick={() => setActiveTab("chunks")}
              className={`px-6 py-3 text-sm font-medium border-b-2 ${
                activeTab === "chunks"
                  ? "border-bargeham-600 text-bargeham-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              متون استخراج شده
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === "metadata" ? (
              <div className="text-gray-600 text-sm">
                متادیتای سند در بالا نمایش داده شده است.
              </div>
            ) : (
              <div className="space-y-4">
                {chunks.length > 0 ? (
                  chunks.map((chunk: any, idx: number) => (
                    <div
                      key={chunk.id || idx}
                      className="border-l-2 border-bargeham-500 pl-4 py-3 bg-gray-50 rounded-r"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-bold bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                          صفحه {chunk.page_number}
                        </span>
                        {chunk.section && (
                          <span className="text-xs text-gray-500">{chunk.section}</span>
                        )}
                      </div>
                      <p className="text-gray-800 whitespace-pre-wrap text-sm leading-relaxed">
                        {chunk.text}
                      </p>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(chunk.text);
                          notify.success("کپی شد", "متن کپی شد");
                        }}
                        className="text-xs text-bargeham-600 hover:text-bargeham-700 mt-1 flex items-center gap-1"
                      >
                        <Copy className="w-3 h-3" />
                        کپی
                      </button>
                    </div>
                  ))
                ) : (
                  <EmptyState
                    icon="📝"
                    title="متنی استخراج نشده"
                    subtitle="این سند هنوز متنی استخراج نشده است."
                  />
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
