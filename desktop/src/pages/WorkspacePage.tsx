import { useEffect, useState } from "react";
import { integrationApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import {
  LayoutDashboard, FileText, Music, BookOpen, GraduationCap,
  Search, Clock, Database,
} from "lucide-react";

export default function WorkspacePage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any>(null);
  const [searching, setSearching] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const s = await integrationApi.workspace();
      setStats(s);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    try {
      const r = await integrationApi.unifiedSearch(query);
      setSearchResults(r);
    } catch (err) { console.error(err); }
    finally { setSearching(false); }
  };

  if (loading) {
    return <AppShell currentPath="#workspace"><div className="flex justify-center py-20"><LoadingSpinner /></div></AppShell>;
  }

  const modules = [
    { label: "اسناد", value: stats?.documents_total ?? 0, sub: `${stats?.documents_ready ?? 0} آماده`, icon: FileText, href: "#documents", color: "bg-blue-100 text-blue-600" },
    { label: "کتابخانه صوتی", value: stats?.audio_total ?? 0, sub: `${stats?.audio_transcribed ?? 0} رونویسی شده`, icon: Music, href: "#audio", color: "bg-purple-100 text-purple-600" },
    { label: "پایگاه دانش", value: stats?.knowledge_bases ?? 0, sub: "KB مستقل", icon: Database, href: "#knowledge", color: "bg-green-100 text-green-600" },
    { label: "آکادمی", value: stats?.academy_courses ?? 0, sub: "دوره", icon: GraduationCap, href: "#academy", color: "bg-orange-100 text-orange-600" },
  ];

  const totalResults = searchResults
    ? (searchResults.documents?.length ?? 0) + (searchResults.audio?.length ?? 0) + (searchResults.knowledge?.length ?? 0)
    : 0;

  return (
    <AppShell currentPath="#workspace">
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <LayoutDashboard className="w-7 h-7 text-bargeham-600" />
            Workspace — نمای یکپارچه
          </h1>
          <p className="text-gray-600 mt-1">جستجو و دسترسی یکپارچه در تمام ماژول‌ها</p>
        </div>

        {/* Module cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {modules.map((m) => {
            const Icon = m.icon;
            return (
              <a key={m.label} href={m.href}
                onClick={(e) => { e.preventDefault(); window.location.hash = m.href; }}
                className="bg-white p-5 rounded-lg shadow-sm border border-gray-200 hover:shadow-md hover:border-bargeham-300 transition-all">
                <div className={`w-10 h-10 rounded-lg ${m.color} flex items-center justify-center mb-3`}>
                  <Icon className="w-5 h-5" />
                </div>
                <p className="text-2xl font-bold text-gray-900">{m.value}</p>
                <p className="text-sm text-gray-600">{m.label}</p>
                <p className="text-xs text-gray-400 mt-1">{m.sub}</p>
              </a>
            );
          })}
        </div>

        {/* Unified search */}
        <form onSubmit={handleSearch} className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
              <input type="text" placeholder="جستجوی یکپارچه در اسناد، صوت و دانش..."
                value={query} onChange={(e) => setQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-bargeham-500" />
            </div>
            <button type="submit" disabled={searching || !query.trim()}
              className="px-5 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700 disabled:opacity-50">
              {searching ? "..." : "جستجو"}
            </button>
          </div>
        </form>

        {/* Search results */}
        {searchResults && (
          <div className="bg-white p-5 rounded-lg border border-gray-200 space-y-4">
            <h2 className="font-semibold text-gray-900">نتایج جستجو ({totalResults})</h2>
            {totalResults === 0 ? (
              <p className="text-gray-500 text-center py-4">نتیجه‌ای یافت نشد</p>
            ) : (
              <div className="space-y-4">
                {searchResults.documents?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-blue-600 mb-2 flex items-center gap-1">
                      <FileText className="w-4 h-4" /> اسناد
                    </h3>
                    {searchResults.documents.map((r: any) => (
                      <div key={r.chunk_id} className="text-sm p-2 border-b border-gray-100">
                        <span className="text-gray-800">{r.text}</span>
                        <span className="text-xs text-gray-400 mr-2">صفحه {r.page}</span>
                      </div>
                    ))}
                  </div>
                )}
                {searchResults.audio?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-purple-600 mb-2 flex items-center gap-1">
                      <Music className="w-4 h-4" /> صوت
                    </h3>
                    {searchResults.audio.map((r: any) => (
                      <div key={r.segment_id} className="text-sm p-2 border-b border-gray-100">
                        <span className="text-gray-800">{r.text}</span>
                        <span className="text-xs text-gray-400 mr-2">[{Math.floor(r.start_seconds)}s]</span>
                      </div>
                    ))}
                  </div>
                )}
                {searchResults.knowledge?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-green-600 mb-2 flex items-center gap-1">
                      <Database className="w-4 h-4" /> دانش
                    </h3>
                    {searchResults.knowledge.map((r: any) => (
                      <div key={r.entry_id} className="text-sm p-2 border-b border-gray-100">
                        <span className="text-gray-800">{r.text}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Recent activity */}
        {stats?.recent?.length > 0 && (
          <div className="bg-white p-5 rounded-lg border border-gray-200">
            <h2 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Clock className="w-5 h-5 text-gray-400" /> فعالیت اخیر
            </h2>
            <div className="space-y-2">
              {stats.recent.map((item: any, i: number) => (
                <div key={i} className="flex items-center gap-3 text-sm">
                  {item.type === "document" ? <FileText className="w-4 h-4 text-blue-500" />
                    : item.type === "audio" ? <Music className="w-4 h-4 text-purple-500" />
                    : <BookOpen className="w-4 h-4 text-green-500" />}
                  <span className="text-gray-800 flex-1">{item.title}</span>
                  <span className="text-xs text-gray-400">{new Date(item.at).toLocaleDateString("fa-IR")}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}