import { useEffect, useState } from "react";
import { creationApi, api } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import EmptyState from "@/components/ui/EmptyState";
import Badge from "@/components/ui/Badge";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { Plus, BookOpen, Play, Clock, FileAudio, RefreshCw } from "lucide-react";

const STATUS: Record<string, { label: string; variant: any }> = {
  draft: { label: "پیش‌نویس", variant: "default" },
  generating: { label: "در حال ساخت", variant: "warning" },
  ready: { label: "آماده", variant: "success" },
  failed: { label: "خطا", variant: "error" },
};

function fmt(sec: number | null): string {
  if (!sec) return "—";
  return `${Math.floor(sec / 60)}:${Math.floor(sec % 60).toString().padStart(2, "0")}`;
}

export default function AudiobookBuilderPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [voices, setVoices] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: "", docId: "", voiceId: "", speed: 1.0 });

  const load = async () => {
    setLoading(true);
    try {
      const [projs, vocs] = await Promise.all([
        creationApi.listAudiobooks(),
        creationApi.listVoices(),
      ]);
      setProjects(projs);
      setVoices(vocs);
      // Load documents for the dropdown
      try {
        const docs = await api.listDocuments({ limit: 100 });
        setDocuments(docs.items || []);
      } catch { /* ignore */ }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!form.title.trim() || !form.docId || !form.voiceId) return;
    try {
      await creationApi.createAudiobook({
        title: form.title,
        source_document_id: form.docId,
        voice_id: form.voiceId,
        speed: form.speed,
      });
      setForm({ title: "", docId: "", voiceId: "", speed: 1.0 });
      setShowForm(false);
      load();
    } catch (err: any) {
      alert("خطا: " + (err.message || "نامشخص"));
    }
  };

  const handleGenerate = async (id: string) => {
    try {
      await creationApi.generateAudiobook(id);
      setTimeout(load, 1000);
    } catch (err: any) {
      alert("خطا: " + (err.message || "نامشخص"));
    }
  };

  return (
    <AppShell currentPath="#audiobook">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <BookOpen className="w-7 h-7 text-bargeham-600" />
              Audiobook Builder
            </h1>
            <p className="text-gray-600 mt-1">تبدیل اسناد به کتاب صوتی با هوش مصنوعی</p>
          </div>
          <button onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 px-4 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700">
            <Plus className="w-4 h-4" /> ساخت Audiobook
          </button>
        </div>

        {showForm && (
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
            <input type="text" placeholder="عنوان کتاب صوتی..." value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-bargeham-500" />
            <select value={form.docId}
              onChange={(e) => setForm({ ...form, docId: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-bargeham-500">
              <option value="">انتخاب سند منبع...</option>
              {documents.map((d: any) => (
                <option key={d.id} value={d.id}>{d.title || d.file_name}</option>
              ))}
            </select>
            <select value={form.voiceId}
              onChange={(e) => setForm({ ...form, voiceId: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-bargeham-500">
              <option value="">انتخاب صدا...</option>
              {voices.map((v: any) => (
                <option key={v.id} value={v.id}>{v.display_name} ({v.language})</option>
              ))}
            </select>
            <div className="flex items-center gap-3">
              <label className="text-sm text-gray-600">سرعت:</label>
              <input type="range" min="0.5" max="2" step="0.1" value={form.speed}
                onChange={(e) => setForm({ ...form, speed: parseFloat(e.target.value) })}
                className="flex-1" />
              <span className="text-sm font-mono w-12">{form.speed}x</span>
            </div>
            <div className="flex gap-3">
              <button onClick={handleCreate}
                disabled={!form.title.trim() || !form.docId || !form.voiceId}
                className="px-5 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700 disabled:opacity-50">
                ایجاد
              </button>
              <button onClick={() => setShowForm(false)}
                className="px-5 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50">
                انصراف
              </button>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-20"><LoadingSpinner /></div>
        ) : projects.length === 0 ? (
          <EmptyState icon="🎧" title="کتاب صوتی‌ای ساخته نشده"
            subtitle="یک سند را انتخاب کنید و به کتاب صوتی تبدیل کنید."
            actionText="ساخت اولین Audiobook" onAction={() => setShowForm(true)} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((p) => {
              const st = STATUS[p.status] || { label: p.status, variant: "default" };
              return (
                <div key={p.id} className="bg-white p-5 rounded-lg shadow-sm border border-gray-200 space-y-3">
                  <div className="flex items-start justify-between">
                    <h3 className="font-bold text-gray-900 truncate">{p.title}</h3>
                    <Badge variant={st.variant}>{st.label}</Badge>
                  </div>
                  <div className="text-sm text-gray-500 space-y-1">
                    <div className="flex items-center gap-2"><Clock className="w-4 h-4" />{fmt(p.total_duration_seconds)}</div>
                    <div className="flex items-center gap-2"><FileAudio className="w-4 h-4" />{p.output_format} · {p.speed}x</div>
                    {p.version > 1 && <div className="text-xs">نسخه {p.version}</div>}
                  </div>
                  {p.status === "draft" && (
                    <button onClick={() => handleGenerate(p.id)}
                      className="w-full flex items-center justify-center gap-2 py-2 bg-bargeham-100 text-bargeham-700 rounded-lg text-sm font-medium hover:bg-bargeham-200">
                      <Play className="w-4 h-4" /> شروع ساخت
                    </button>
                  )}
                  {p.status === "generating" && (
                    <div className="flex items-center justify-center gap-2 py-2 text-yellow-600 text-sm">
                      <RefreshCw className="w-4 h-4 animate-spin" /> در حال ساخت...
                    </div>
                  )}
                  {p.status === "ready" && p.output_path && (
                    <audio controls src={`http://localhost:8000/audio/${p.id}/stream`} className="w-full" />
                  )}
                  {p.status === "failed" && p.error_message && (
                    <p className="text-xs text-red-500 bg-red-50 p-2 rounded">{p.error_message}</p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}