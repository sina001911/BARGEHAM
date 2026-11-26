import React, { useEffect, useState } from "react";
import { useStore } from "@/store/useStore";
import { api } from "@/lib/api";
import DocumentCard from "@/components/ui/DocumentCard";
import EmptyState from "@/components/ui/EmptyState";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { Search, Plus, Folder } from "lucide-react";
import { notify } from "@/lib/api";

export default function DocumentsPage() {
  const { documents, total, loading, error, fetchDocuments, setCurrentFolder, currentFolder } = useStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [debounceTimer, setDebounceTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    fetchDocuments(selectedFolder, searchQuery);
  }, [fetchDocuments, selectedFolder, searchQuery]);

  const handlePickFolder = async () => {
    try {
      const folder = await api.pickFolder();
      if (folder) {
        setSelectedFolder(folder.id);
        setCurrentFolder(folder);
      }
    } catch (err: any) {
      notify.error("خطا در انتخاب پوشه", err.message);
    }
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    if (debounceTimer) clearTimeout(debounceTimer);
    const timer = setTimeout(() => {
      fetchDocuments(selectedFolder, e.target.value);
    }, 300);
    setDebounceTimer(timer);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">اسناد</h1>
          <p className="text-gray-600">مدیریت و مشاهده اسناد ذخیره‌شده</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handlePickFolder}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <Folder className="w-4 h-4" />
            انتخاب پوشه
          </button>
          <a
            href="#upload"
            onClick={(e) => {
              e.preventDefault();
              window.location.hash = "#upload";
            }}
            className="flex items-center gap-2 px-4 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            بارگذاری جدید
          </a>
        </div>
      </div>

      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-xl">
          <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="جستجو در عنوان، نام فایل و محتوای اسناد..."
            value={searchQuery}
            onChange={handleSearch}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bargeham-500 focus:border-bargeham-500 outline-none"
          />
        </div>
      </div>

      {loading && (
        <div className="flex justify-center py-10">
          <LoadingSpinner />
        </div>
      )}

      {error && !loading && (
        <div className="p-4 rounded bg-red-50 text-red-700 text-sm border border-red-100">
          {error}
        </div>
      )}

      {documents.length === 0 && !loading && !error && (
        <EmptyState
          icon="📄"
          title="سندی ثبت نشده است"
          subtitle="هنوز سندی در سیستم ثبت نشده است. می‌توانید اولین سند را بارگذاری کنید."
          actionText="بارگذاری سند اول"
          onAction={() => {
            window.location.hash = "#upload";
          }}
        />
      )}

      {documents.length > 0 && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
            <span className="text-sm font-medium text-gray-600">{total} سند یافته شده</span>
          </div>
          <div className="divide-y divide-gray-100">
            {documents.map((doc) => (
              <DocumentCard key={doc.id} doc={doc} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
