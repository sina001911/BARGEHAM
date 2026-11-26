"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!file) {
      setError("لطفاً یک فایل انتخاب کنید");
      return;
    }
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);
    if (title) formData.append("title", title);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/documents`, {
        method: "POST",
        body: formData,
        headers: {
          Authorization: `Bearer ${typeof window !== "undefined" ? localStorage.getItem("auth-storage") : null}`,
        },
      });
      if (!res.ok) throw new Error((await res.json()).message || "خطا در بارگذاری");
      const data = await res.json();
      setSuccess(`سند "${data.document_id}" با موفقیت بارگذاری شد و برای پردازش به صف اضافه شد.`);
      setFile(null);
      setTitle("");
    } catch (err: any) {
      setError(err.message || "خطا در بارگذاری");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">بارگذاری سند جدید</h1>
      {error && <div className="p-3 rounded bg-red-50 text-red-700 text-sm">{error}</div>}
      {success && <div className="p-3 rounded bg-green-50 text-green-700 text-sm">{success}</div>}
      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg border shadow space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">عنوان سند</label>
          <input
            type="text"
            className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="اختياري - از نام فایل استفاده می‌شود"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">فایل</label>
          <input
            type="file"
            accept=".pdf,.docx,.xlsx,.txt,.png,.jpg,.jpeg,.tiff,.webp"
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !file}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-70"
        >
          {loading ? "در حال بارگذاری..." : "بارگذاری سند"}
        </button>
      </form>
    </div>
  );
}
