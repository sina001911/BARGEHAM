"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface Document {
  id: string;
  title: string;
  file_name: string;
  status: string;
  version: number;
  created_at: string;
}

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");

  useEffect(() => {
    api
      .get<{ items: Document[]; total: number }>("/documents", {
        query: { limit: 100, q },
      })
      .then((r) => setDocs(r.items))
      .finally(() => setLoading(false));
  }, [q]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">اسناد</h1>
        <input
          type="text"
          placeholder="جستجو در عنوان..."
          className="border rounded px-3 py-2 w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="h-64 flex items-center justify-center text-gray-400">در حال بارگذاری...</div>
      ) : docs.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          سندی یافت نشد.{" "}
          <Link href="/upload" className="text-blue-600 hover:underline">بارگذاری سند جدید</Link>
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden bg-white">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="px-4 py-3 text-sm font-medium">عنوان</th>
                <th className="px-4 py-3 text-sm font-medium">نام فایل</th>
                <th className="px-4 py-3 text-sm font-medium">نسخه</th>
                <th className="px-4 py-3 text-sm font-medium">وضعیت</th>
                <th className="px-4 py-3 text-sm font-medium">تاریخ</th>
                <th className="px-4 py-3 text-sm font-medium">عملیات</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {docs.map((d) => (
                <tr key={d.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{d.title}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{d.file_name}</td>
                  <td className="px-4 py-3 text-sm">{d.version}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      d.status === "ready" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
                    }`}>{d.status}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">{new Date(d.created_at).toLocaleDateString("fa-IR")}</td>
                  <td className="px-4 py-3">
                    <Link href={`/documents/${d.id}`} className="text-blue-600 hover:underline">مشاهده</Link>
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
