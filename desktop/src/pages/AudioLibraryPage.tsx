import { useEffect, useRef, useState } from "react";
import { audioApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import EmptyState from "@/components/ui/EmptyState";
import Badge from "@/components/ui/Badge";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { Upload, Music, Search, Play, Trash2, Clock, FileAudio } from "lucide-react";

const STATUS_LABELS: Record<string, { label: string; variant: any }> = {
  uploading: { label: "در حال بارگذاری", variant: "warning" },
  processing: { label: "در حال پردازش", variant: "warning" },
  ready: { label: "آماده", variant: "success" },
  transcribed: { label: "رونویسی شده", variant: "info" },
  failed: { label: "خطا", variant: "error" },
};

function fmtDuration(sec: number | null): string {
  if (!sec) return "—";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function AudioLibraryPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [q, setQ] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await audioApi.list({ q: q || undefined, limit: 100 });
      setItems(res.items);
    } catch (err) {
      console.error("Failed to load audio:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    setUploading(true);
    try {
      for (const file of Array.from(e.target.files)) {
        await audioApi.upload(file, file.name);
      }
      await load();
    } catch (err: any) {
      alert("خطا در بارگذاری: " + (err.message || "نامشخص"));
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("حذف این فایل صوتی؟")) return;
    try {
      await audioApi.delete(id);
      setItems((prev) => prev.filter((a) => a.id !== id));
    } catch (err: any) {
      alert("خطا: " + (err.message || "نامشخص"));
    }
  };

  return (
    <AppShell currentPath="#audio">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Music className="w-7 h-7 text-bargeham-600" />
              کتابخانه صوتی
            </h1>
            <p className="text-gray-600 mt-1">بارگذاری، پخش و رونویسی فایل‌های صوتی — فارسی و انگلیسی</p>
          </div>
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="flex items-center gap-2 px-4 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700 disabled:opacity-50"
          >
            <Upload className="w-4 h-4" />
            {uploading ? "در حال بارگذاری..." : "بارگذاری صدا"}
          </button>
          <input ref={fileRef} type="file" accept="audio/*,.mp3,.wav,.ogg,.m4a,.flac" multiple
            onChange={handleUpload} className="hidden" />
        </div>

        {/* Search */}
        <form onSubmit={(e) => { e.preventDefault(); load(); }}
          className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="جستجو در عنوان فایل‌های صوتی..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-bargeham-500"
            />
          </div>
        </form>

        {/* List */}
        {loading ? (
          <div className="flex justify-center py-20"><LoadingSpinner /></div>
        ) : items.length === 0 ? (
          <EmptyState
            icon="🎵"
            title="فایل صوتی‌ای وجود ندارد"
            subtitle="اولین فایل صوتی را بارگذاری کنید تا رونویسی و پردازش شود."
            actionText="بارگذاری صدا"
            onAction={() => fileRef.current?.click()}
          />
        ) : (
          <div className="space-y-3">
            {items.map((audio) => {
              const st = STATUS_LABELS[audio.status] || { label: audio.status, variant: "default" };
              return (
                <div key={audio.id} className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-bargeham-50 flex items-center justify-center shrink-0">
                    <FileAudio className="w-6 h-6 text-bargeham-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 truncate">{audio.title}</div>
                    <div className="text-sm text-gray-500 flex items-center gap-3 mt-0.5">
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{fmtDuration(audio.duration_seconds)}</span>
                      {audio.language && <span>· {audio.language}</span>}
                      {audio.has_transcript && <span className="text-green-600">· رونویسی موجود</span>}
                    </div>
                  </div>
                  <Badge variant={st.variant}>{st.label}</Badge>
                  <a href={`#audio/player/${audio.id}`}
                    onClick={(e) => { e.preventDefault(); window.location.hash = `#audio/player/${audio.id}`; }}
                    className="p-2 rounded-lg bg-bargeham-100 text-bargeham-700 hover:bg-bargeham-200">
                    <Play className="w-5 h-5" />
                  </a>
                  <button onClick={() => handleDelete(audio.id)}
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors">
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}