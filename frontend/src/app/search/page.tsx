"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Array<{
    chunk_id: string;
    document_id: string;
    page_number: number;
    text: string;
    score: number;
  }>>([]);
  const [loading, setLoading] = useState(false);

  async function handleSearch() {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await api.get<Array<{ chunk_id: string; document_id: string; page_number: number; text: string; score: number }>>(
        "/search/chunks",
        { query: { q: query, limit: 30 } }
      );
      setResults(res);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-5">
      <h1 className="text-2xl font-bold">جستجوی ترکیبی در اسناد</h1>
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="متن مورد نظر را بنویسید..."
          className="flex-1 border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && handleSearch()}
        />
        <button onClick={handleSearch} disabled={loading} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-70">
          جستجو
        </button>
      </div>
      {loading && <div className="text-gray-500">در حال جستجو...</div>}
      {results.length === 0 && query.trim() && !loading && (
        <div className="text-center py-8 text-gray-500">نتیجه‌ای یافت نشد</div>
      )}
      <div className="space-y-3">
        {results.map((r) => (
          <div key={r.chunk_id} className="border rounded-lg p-4 bg-white">
            <div className="text-xs text-gray-500 mb-1">
              سند {r.document_id} • صفحه {r.page_number} • رتبه {r.score}
            </div>
            <div className="text-gray-800 whitespace-pre-wrap">{r.text}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
