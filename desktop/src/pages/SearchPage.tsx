import { useState } from "react";
import { useStore } from "@/store/useStore";
import { api } from "@/lib/api";
import { Search, FileText, Clock } from "lucide-react";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const { setSearchResults } = useStore();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const searchResults = await api.searchDocuments({ q: query, limit: 30 });
      setResults(searchResults);
      setSearchResults(searchResults);
    } catch (err: any) {
      console.error("Search failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">جستجوی هوشمند</h1>
          <p className="text-gray-600">
            جستجوی ترکیبی (متن کامل + برداری) در اسناد index شده
          </p>
        </div>
        <a
          href="#ask"
          onClick={(e) => {
            e.preventDefault();
            window.location.hash = "#ask";
          }}
          className="flex items-center gap-2 px-4 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700 transition-colors"
        >
          <MessageCircleIcon className="w-4 h-4" />
          پرشو از هوش مصنوعی
        </a>
      </div>

      <form onSubmit={handleSearch} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="متن مورد نظر را جستجو کنید..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && e.currentTarget.form?.requestSubmit?.()}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bargeham-500 focus:border-bargeham-500 outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700 transition-colors disabled:opacity-70"
          >
            {loading ? "در حال جستجو..." : "جستجو"}
          </button>
        </div>
      </form>

      {loading && (
        <div className="flex justify-center py-10">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {results.length === 0 && !loading && query.trim() && (
        <div className="flex flex-col items-center justify-center py-20 text-gray-500">
          <span className="text-4xl mb-4">🔍</span>
          <p>Netیجه‌ای یافت نشد</p>
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider mb-3">
            نتایج ({results.length})
          </h2>
          {results.map((result: any, index: number) => (
            <div key={result.chunk_id || index} className="bg-white p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-1">
                  <span className="text-xs font-bold bg-gray-100 text-gray-600 px-2 py-1 rounded">
                    {index + 1}
                  </span>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                    <span className="flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      <span>سند {result.document_id}</span>
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>صفحه {result.page_number}</span>
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-600">
                      رتبه {result.score?.toFixed(2) || "—"}
                    </span>
                  </div>
                  <p className="text-gray-800 whitespace-pre-wrap">{result.text}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MessageCircleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M8 12h.01M12 12h.01M16 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}
