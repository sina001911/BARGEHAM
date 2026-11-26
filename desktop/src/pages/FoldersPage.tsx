import React, { useState, useEffect } from "react";
import { useStore } from "@/store/useStore";
import { api } from "@/lib/api";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { Folder, Plus, FolderPlus, FolderOpen } from "lucide-react";

interface FolderRow {
  id: string;
  name: string;
  parent_id: string | null;
  owner_id: string | null;
  created_at: string;
}

export default function FoldersPage() {
  const [folders, setFolders] = useState<FolderRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newFolderName, setNewFolderName] = useState("");
  const [creating, setCreating] = useState(false);
  const { setCurrentFolder } = useStore();

  useEffect(() => {
    loadFolders();
  }, []);

  async function loadFolders() {
    setLoading(true);
    setError(null);
    try {
      const result = await api.listFolders();
      setFolders(result as FolderRow[]);
    } catch (err: any) {
      setError(err.message || "Failed to load folders");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateFolder(e: React.FormEvent) {
    e.preventDefault();
    if (!newFolderName.trim()) return;
    setCreating(true);
    try {
      const newFolder = await api.createFolder({
        name: newFolderName.trim(),
      });
      setFolders((prev) => [...prev, newFolder as FolderRow]);
      setNewFolderName("");
    } catch (err: any) {
      setError(err.message || "Failed to create folder");
    } finally {
      setCreating(false);
    }
  }

  async function handleSelectFolder(folder: FolderRow) {
    setCurrentFolder(folder);
  }

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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">پوشه‌ها</h1>
        <p className="text-gray-600">
          مدیریت پوشه‌های اسناد و دسته‌بندی فایل‌ها
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <form onSubmit={handleCreateFolder} className="flex items-center gap-2">
          <input
            type="text"
            placeholder="نام پوشه جدید..."
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bargeham-500 focus:border-bargeham-500 outline-none"
          />
          <button
            type="submit"
            disabled={creating || !newFolderName.trim()}
            className="px-4 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700 disabled:opacity-70 transition-colors"
          >
            {creating ? "در حال ایجاد..." : "ایجاد پوشه"}
          </button>
        </form>
      </div>

      {folders.length === 0 ? (
        <EmptyState
          icon="📁"
          title="پوشه‌ای ثبت نشده است"
          subtitle="اولین پوشه خود را ایجاد کنید تا اسناد را دسته‌بندی کنید."
        />
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <table className="w-full text-left">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                  نام پوشه
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                  گذاشته شده در
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">
                  عملیات
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {folders.map((folder) => (
                <tr
                  key={folder.id}
                  className="hover:bg-gray-50 transition-colors cursor-pointer group"
                  onClick={() => handleSelectFolder(folder)}
                >
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    <FolderOpen className="w-4 h-4 text-gray-400 mr-2 inline-block" />
                    {folder.name}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {new Date(folder.created_at).toLocaleDateString("fa-IR")}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-xs font-medium text-blue-600 hover:text-blue-800 underline">
                      انتخاب
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
