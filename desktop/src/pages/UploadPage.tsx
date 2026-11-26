import React, { useState } from "react";
import { useStore } from "@/store/useStore";
import { api } from "@/lib/api";
import { Upload, FileText, Folder, Clock } from "lucide-react";

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<Record<string, number>>({});
  const [results, setResults] = useState<Array<{ id: string; name: string; status: string }>>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const { addDocument } = useStore();

  const handleFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handlePickFolder = async () => {
    try {
      const folderPath = await api.pickFolder();
      if (folderPath) {
        setSelectedFolder(folderPath);
      }
    } catch (err: any) {
      console.error("Failed to pick folder:", err);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0) return;

    setUploading(true);
    setResults([]);

    for (const file of files) {
      setProgress((prev) => ({ ...prev, [file.name]: 0 }));

      try {
        const result = await api.uploadDocument({
          file: file,
          title: file.name,
          folder_id: selectedFolder,
        });

        setResults((prev) => [
          ...prev,
          { id: result.document_id, name: file.name, status: result.status },
        ]);

        addDocument({
          id: result.document_id,
          path: file.name,
          file_name: file.name,
          file_size: file.size,
          mime_type: file.type,
          document_type: "other",
          status: result.status,
          version: 1,
          page_count: null,
          language: null,
          has_text_layer: false,
          ocr_confidence: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          folder_id: selectedFolder,
          owner_id: null,
          chunks: [],
        });

        setProgress((prev) => ({ ...prev, [file.name]: 100 }));
      } catch (err: any) {
        setProgress((prev) => ({ ...prev, [file.name]: 0 }));
        console.error("Upload failed:", err);
      }
    }

    setUploading(false);
    setFiles([]);
  };

  const allowedExtensions = [".pdf", ".docx", ".xlsx", ".txt", ".png", ".jpg", ".jpeg", ".tiff", ".webp"];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">بارگذاری سند</h1>
        <p className="text-gray-600">
          بارگذاری اسناد برای پردازش، استخراج متن و تبدیل به قابل جستجو
        </p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <form onSubmit={handleUpload} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              انتخاب فایل
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-bargeham-500 hover:bg-gray-50 transition-colors">
              <input
                id="file-input"
                type="file"
                multiple
                onChange={handleFilesChange}
                className="sr-only"
              />
              <label
                htmlFor="file-input"
                className="flex flex-col items-center gap-2 cursor-pointer"
              >
                <Upload className="w-8 h-8 text-gray-400" />
                <p className="text-sm text-gray-600">کلیک کنید یا فایل‌ها را بکشید و رها کنید</p>
                <p className="text-xs text-gray-500">
                  PDF, DOCX, XLSX, TXT, PNG, JPG, JPEG, TIFF, WEBP
                </p>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              پوشه مقصد (اختیاری)
            </label>
            <div className="flex items-center gap-3">
              <button
                onClick={handlePickFolder}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <Folder className="w-4 h-4" />
                انتخاب پوشه
              </button>
              {selectedFolder && (
                <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                  پوشه elect شده
                </span>
              )}
            </div>
          </div>

          {files.length > 0 && (
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">فایل‌های انتخاب شده ({files.length})</h3>
              <ul className="space-y-2">
                {files.map((file) => (
                  <li key={file.name} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-700 truncate max-w-[200px]">{file.name}</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {(file.size / 1024).toFixed(1)} KB
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <button
            type="submit"
            disabled={files.length === 0 || uploading}
            className="w-full bg-bargeham-600 text-white py-3 rounded-lg font-semibold hover:bg-bargeham-700 disabled:opacity-70 transition-colors flex items-center justify-center gap-2"
          >
            {uploading ? (
              <React.Fragment>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>در حال بارگذاری...</span>
              </React.Fragment>
            ) : (
              <React.Fragment>
                <Upload className="w-4 h-4" />
                <span>بارگذاری {files.length} فایل</span>
              </React.Fragment>
            )}
          </button>
        </form>
      </div>

      {results.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">نتایج بارگذاری</h3>
          <div className="space-y-2">
            {results.map((result) => (
              <div key={result.id} className="flex items-center justify-between p-3 bg-gray-50 rounded border border-gray-100">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-700 truncate">{result.name}</span>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${getBadgeColor(result.status)}`}>
                  {result.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function getBadgeColor(status: string) {
  switch (status) {
    case "ready":
      return "bg-green-100 text-green-700";
    case "processing":
      return "bg-yellow-100 text-yellow-700 animate-pulse";
    case "error":
    case "ocr_failed":
      return "bg-red-100 text-red-700";
    default:
      return "bg-gray-100 text-gray-600";
  }
}
