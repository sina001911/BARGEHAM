"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface Document {
  id: string;
  title: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  status: string;
  language: string | null;
  page_count: number | null;
  ocr_confidence: number | null;
  created_at: string;
}

interface Chunk {
  id: string;
  page_number: number;
  text: string;
}

export default async function DocumentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [doc, setDoc] = useState<Document | null>(null);
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<Document>(`/documents/${id}`),
      api.get<Chunk[]>(`/documents/${id}/chunks`, { query: { limit: 500 } }),
    ])
      .then(([d, c]) => {
        setDoc(d);
        setChunks(c);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="py-10 text-center text-gray-400">در حال بارگذاری...</div>;
  if (!doc) return <div className="py-10 text-center text-red-500">سند یافت نشد</div>;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <Link href="/documents" className="text-sm text-blue-600 hover:underline">
          ← بازگشت به لیست
        </Link>
      </div>

      <div className="bg-white p-6 rounded-lg border shadow">
        <h1 className="text-xl font-bold mb-2">{doc.title}</h1>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm text-gray-600">
          <div><span className="font-medium">نام فایل:</span> {doc.file_name}</div>
          <div><span className="font-medium">اندازه:</span> {(doc.file_size / 1024).toFixed(1)} KB</div>
          <div><span className="font-medium">وضعیت:</span> {doc.status}</div>
          <div><span className="font-medium">صفحات:</span> {doc.page_count ?? "—"}</div>
          <div><span className="font-medium">زبان:</span> {doc.language ?? "—"}</div>
          <div><span className="font-medium">اعتماد OCR:</span> {doc.ocr_confidence?.toFixed(2) ?? "—"}</div>
        </div>
        <div className="mt-4">
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/documents/${doc.id}/download`}
            className="text-blue-600 hover:underline text-sm"
            download
          >
            ↓ دانلود فایل اصلی
          </a>
        </div>
      </div>

      <div className="border rounded-lg bg-white p-5">
        <h2 className="text-lg font-bold mb-3 border-b pb-2">متن استخراج‌شده</h2>
        {chunks.length === 0 ? (
          <div className="text-gray-500 py-4">متنی استخراج نشده است.</div>
        ) : (
          <div className="space-y-4 text-gray-800 whitespace-pre-wrap">
            {chunks.map((c) => (
              <div key={c.id} className="border-l-2 border-blue-500 pl-4 py-2">
                <span className="text-xs text-gray-400">صفحه {c.page_number}</span>
                <p className="mt-1">{c.text}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
