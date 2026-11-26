import { useState } from "react";
import { api } from "@/lib/api";
import { MessageCircle, Send, Clock, FileText } from "lucide-react";

export default function AskPage() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [documentId, setDocumentId] = useState("");

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await api.askQuestion({
        query,
        document_id: documentId || undefined,
        limit: 8,
      });
      setAnswer(response.answer);
    } catch (err: any) {
      setAnswer("خطا در دریافت پاسخ: " + (err.message || "خطای ناشناس"));
    } finally {
      setLoading(false);
    }
  };

  const handleStreamAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setAnswer("در حال تولید پاسخ...");
    try {
      const response = await api.askQuestion({
        query,
        document_id: documentId || undefined,
        limit: 8,
      });
      setAnswer(response.answer);
    } catch (err: any) {
      setAnswer("خطا در دریافت پاسخ: " + (err.message || "خطای ناشناس"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">پرسش و پاسخ هوشمند</h1>
          <p className="text-gray-600">
            پرسیدن سوال از اسناد و دریافت پاسخ با ارجاع به منبع
          </p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <form onSubmit={handleAsk} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              سوال خود را بپرسید
            </label>
            <textarea
              rows={4}
              placeholder="مثال: چکինգ últimos دو ماه چقدر بود؟"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-bargeham-500 focus:border-bargeham-500 outline-none"
            />
          </div>

          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <label className="block text-xs font-medium text-gray-500 mb-1">
                فیلتر بر اساس سند (اختیاری)
              </label>
              <input
                type="text"
                placeholder="شناسه سند..."
                value={documentId}
                onChange={(e) => setDocumentId(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-bargeham-500 focus:border-bargeham-500 outline-none"
              />
            </div>
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="flex-1 bg-bargeham-600 text-white py-3 rounded-lg font-semibold hover:bg-bargeham-700 disabled:opacity-70 transition-colors"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>در حال پردازش...</span>
                </>
              ) : (
                <>
                  <MessageCircle className="w-4 h-4 mr-2" />
                  پاسخ (یک-shot)
                </>
              )}
            </button>
            <button
              onClick={handleStreamAsk}
              disabled={loading || !query.trim()}
              className="flex-1 bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-70 transition-colors"
            >
              <Clock className="w-4 h-4 mr-2" />
              پاسخ(stream)
            </button>
          </div>
        </form>
      </div>

      {answer && (
        <div className="bg-gray-900 text-green-100 p-5 rounded-lg shadow-lg break-words whitespace-pre-wrap font-mono text-sm">
          <div className="flex items-center gap-2 mb-3 text-xs text-gray-400 uppercase tracking-wider">
            <FileText className="w-3 h-3" />
            پاسخ هوش مصنوعی
          </div>
          {answer}
        </div>
      )}

      {loading && !answer && (
        <div className="flex justify-center py-10 text-gray-500">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}
    </div>
  );
}
