"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function AskPage() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleAsk() {
    if (!query.trim()) return;
    setLoading(true);
    setAnswer("");
    try {
      const res = await api.post<{ answer: string }>("/ask", { query });
      setAnswer(res.answer);
    } catch (err: any) {
      setAnswer("خطا: " + (err.message || "ارتباط با سرویس AI برقرار نشد"));
    } finally {
      setLoading(false);
    }
  }

  async function handleStream() {
    if (!query.trim()) return;
    setLoading(true);
    setAnswer("");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/ask/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${typeof window !== "undefined" ? localStorage.getItem("auth-storage") : null}`,
        },
        body: JSON.stringify({ query }),
      });
      if (!res.ok || !res.body) throw new Error("Stream failed");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        setAnswer((prev) => prev + decoder.decode(value, { stream: true }));
      }
    } catch (err: any) {
      setAnswer("خطا در Streaming: " + (err.message || "نامشخص"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-5">
      <h1 className="text-2xl font-bold">پرسش و پاسخ هویتی (RAG)</h1>
      <div className="bg-white p-5 rounded-lg border shadow">
        <textarea
          className="w-full h-32 border rounded p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 mb-3"
          placeholder="سوال خود را درباره اسناد بپرسید..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="flex gap-2">
          <button onClick={handleAsk} disabled={loading} className="flex-1 bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-70">
            پاسخ (یک-shot)
          </button>
          <button onClick={handleStream} disabled={loading} className="flex-1 bg-green-600 text-white py-2 rounded hover:bg-green-700 disabled:opacity-70">
            پاسخ ز(stream)
          </button>
        </div>
      </div>
      {loading && <div className="text-gray-500">در حال تولید پاسخ...</div>}
      {answer && (
        <div className="bg-gray-900 text-green-100 p-5 rounded-lg break-words whitespace-pre-wrap font-mono text-sm">
          {answer}
        </div>
      )}
    </div>
  );
}
