"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

interface Document {
  id: string;
  title: string;
  file_name: string;
  status: string;
  created_at: string;
}

export default function DashboardPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuthStore();

  useEffect(() => {
    api
      .get<{ items: Document[]; total: number }>("/documents", { query: { limit: 5 } })
      .then((r) => setDocs(r.items))
      .catch(() => setDocs([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">داشبورد</h1>
        <p className="text-gray-600">
          خوش آمدید، {user?.full_name || "کاربر"}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="مجموع اسناد" value={docs.length} icon="📄" />
        <StatCard label="در حال پردازش" value={docs.filter((d) => d.status === "processing").length} icon="⏳" />
        <StatCard label="آماده" value={docs.filter((d) => d.status === "ready").length} icon="✅" />
      </div>

      <div className="border rounded-lg bg-white p-4">
        <h2 className="text-lg font-bold mb-4 border-b pb-2">اسناد اخیر</h2>
        {loading ? (
          <div className="h-32 flex items-center justify-center text-gray-400">در حال بارگذاری...</div>
        ) : docs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            سندی ثبت نشده است. <Link href="/upload" className="text-blue-600 hover:underline">سند جدید بارگذاری کنید</Link>
          </div>
        ) : (
          <ul className="divide-y">
            {docs.map((d) => (
              <li key={d.id} className="py-3 flex items-center gap-4">
                <span className="text-gray-400 text-sm">📎</span>
                <div className="flex-1">
                  <div className="font-medium">{d.title}</div>
                  <div className="text-xs text-gray-500">{d.file_name}</div>
                </div>
                <span className={`text-xs font-medium px-2 py-1 rounded ${
                  d.status === "ready" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
                }`}>{d.status}</span>
                <Link href={`/documents/${d.id}`} className="text-sm text-blue-600 hover:underline">
                  مشاهده
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, icon }: { label: string; value: number; icon: string }) {
  return (
    <div className="bg-white p-4 rounded-lg border shadow-sm">
      <div className="text-2xl">{icon}</div>
      <div className="text-2xl font-bold mt-2">{value}</div>
      <div className="text-sm text-gray-500">{label}</div>
    </div>
  );
}
