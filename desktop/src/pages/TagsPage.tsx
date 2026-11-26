import React, { useState, useEffect } from "react";
import { useStore } from "@/store/useStore";
import { api } from "@/lib/api";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { Tag, Plus, Tag as TagIcon } from "lucide-react";

interface TagRow {
  id: string;
  name: string;
  color: string | null;
  created_at: string;
}

export default function TagsPage() {
  const [tags, setTags] = useState<TagRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newTagName, setNewTagName] = useState("");
  const [newTagColor, setNewTagColor] = useState("#3b82f6");
  const [creating, setCreating] = useState(false);

  const COLORS = [
    "#3b82f6", // blue
    "#ef4444", // red
    "#10b981", // emerald
    "#f59e0b", // amber
    "#8b5cf6", // violet
    "#ec4899", // pink
    "#06b6d4", // cyan
    "#84cc16", // lime
  ];

  useEffect(() => {
    loadTags();
  }, []);

  async function loadTags() {
    setLoading(true);
    setError(null);
    try {
      const result = await api.listTags();
      setTags(result as TagRow[]);
    } catch (err: any) {
      setError(err.message || "Failed to load tags");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateTag(e: React.FormEvent) {
    e.preventDefault();
    if (!newTagName.trim()) return;
    setCreating(true);
    try {
      const newTag = await api.createTag({
        name: newTagName.trim(),
        color: newTagColor,
      });
      setTags((prev) => [...prev, newTag as TagRow]);
      setNewTagName("");
      setNewTagColor("#3b82f6");
    } catch (err: any) {
      setError(err.message || "Failed to create tag");
    } finally {
      setCreating(false);
    }
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
        <h1 className="text-2xl font-bold text-gray-900">برچسب‌ها</h1>
        <p className="text-gray-600">
          مدیریت برچسب‌ها برای دسته‌بندی و جستجوی سریع اسناد
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <form onSubmit={handleCreateTag} className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">نام برچسب:</label>
            <input
              type="text"
              placeholder="نام برچسب جدید..."
              value={newTagName}
              onChange={(e) => setNewTagName(e.target.value)}
              className="w-48 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bargeham-500 focus:border-bargeham-500 outline-none"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">رنگ:</label>
            <div className="flex gap-1">
              {COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setNewTagColor(color)}
                  className={`w-6 h-6 rounded-full border border-white ${color === newTagColor ? "ring-2 ring-gray-400" : ""} shadow-sm`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
          </div>
          <button
            type="submit"
            disabled={creating || !newTagName.trim()}
            className="px-4 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700 disabled:opacity-70 transition-colors"
          >
            {creating ? "در حال ایجاد..." : "ایجاد برچسب"}
          </button>
        </form>
      </div>

      {tags.length === 0 ? (
        <EmptyState
          icon="🏷️"
          title="برچسبی ثبت نشده است"
          subtitle="اولین برچسب خود را ایجاد کنید تا اسناد را برچسب‌گذاری کنید."
        />
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex flex-wrap gap-4">
            {tags.map((tag) => (
              <div
                key={tag.id}
                className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
              >
                <span
                  className="inline-block w-3 h-3 rounded-full"
                  style={{ backgroundColor: tag.color || "#3b82f6" }}
                />
                <span className="text-sm text-gray-800">{tag.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
