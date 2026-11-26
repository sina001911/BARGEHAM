import { useEffect, useRef, useState } from "react";
import { audioApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import Badge from "@/components/ui/Badge";
import { ArrowLeft, Play, Pause, SkipBack, SkipForward, FileText, List } from "lucide-react";

function fmt(sec: number | null | undefined): string {
  if (!sec || sec < 0) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function AudioPlayerPage() {
  const audioId = typeof window !== "undefined" ? window.location.hash.match(/player\/([^/]+)/)?.[1] : null;
  const audioRef = useRef<HTMLAudioElement>(null);
  const [audio, setAudio] = useState<any>(null);
  const [chapters, setChapters] = useState<any[]>([]);
  const [segments, setSegments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [tab, setTab] = useState<"chapters" | "transcript">("transcript");
  const [newChapterTitle, setNewChapterTitle] = useState("");

  const load = async () => {
    if (!audioId) return;
    setLoading(true);
    try {
      const [a, ch, seg] = await Promise.all([
        audioApi.get(audioId),
        audioApi.listChapters(audioId),
        audioApi.listSegments(audioId),
      ]);
      setAudio(a);
      setChapters(ch);
      setSegments(seg);
      setDuration(a.duration_seconds || 0);
    } catch (err) {
      console.error("Failed to load audio:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [audioId]); // eslint-disable-line react-hooks/exhaustive-deps

  const togglePlay = () => {
    const el = audioRef.current;
    if (!el) return;
    if (playing) el.pause();
    else el.play();
  };

  const seek = (sec: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = sec;
      setCurrentTime(sec);
    }
  };

  const skipChapter = (dir: 1 | -1) => {
    const sorted = [...chapters].sort((a, b) => a.start_seconds - b.start_seconds);
    if (dir === 1) {
      const next = sorted.find((c) => c.start_seconds > currentTime + 1);
      if (next) seek(next.start_seconds);
    } else {
      const prev = [...sorted].reverse().find((c) => c.start_seconds < currentTime - 1);
      if (prev) seek(prev.start_seconds);
      else seek(0);
    }
  };

  const handleAddChapter = async () => {
    if (!audioId || !newChapterTitle.trim()) return;
    try {
      const ch = await audioApi.createChapter(audioId, newChapterTitle, currentTime);
      setChapters((prev) => [...prev, ch]);
      setNewChapterTitle("");
    } catch (err: any) {
      alert("خطا: " + (err.message || "نامشخص"));
    }
  };

  const activeChapter = [...chapters]
    .sort((a, b) => a.start_seconds - b.start_seconds)
    .reverse()
    .find((c) => c.start_seconds <= currentTime);

  if (loading) {
    return <AppShell currentPath="#audio"><div className="flex justify-center py-20"><LoadingSpinner /></div></AppShell>;
  }

  if (!audio) {
    return (
      <AppShell currentPath="#audio">
        <div className="flex flex-col items-center justify-center py-20 text-gray-500">
          <span className="text-5xl mb-4">🔍</span>
          <p className="text-lg font-medium">فایل صوتی یافت نشد</p>
          <button onClick={() => { window.location.hash = "#audio"; }}
            className="mt-4 px-4 py-2 bg-bargeham-600 text-white rounded-lg hover:bg-bargeham-700">
            بازگشت
          </button>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell currentPath="#audio">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button onClick={() => { window.location.hash = "#audio"; }}
            className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-gray-900 truncate">{audio.title}</h1>
            <div className="text-sm text-gray-500 flex items-center gap-3 mt-0.5">
              <span>{fmt(duration)}</span>
              {audio.language && <Badge variant="info">{audio.language}</Badge>}
              {activeChapter && <span className="text-bargeham-600">· {activeChapter.title}</span>}
            </div>
          </div>
        </div>

        {/* Player */}
        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200 space-y-4">
          <audio
            ref={audioRef}
            src={audioApi.streamUrl(audio.id)}
            onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
            onLoadedMetadata={(e) => setDuration(e.currentTarget.duration || duration)}
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onEnded={() => setPlaying(false)}
            className="w-full"
          />
          <div className="flex items-center justify-center gap-4">
            <button onClick={() => skipChapter(-1)} className="p-2 text-gray-600 hover:text-bargeham-600">
              <SkipBack className="w-6 h-6" />
            </button>
            <button onClick={togglePlay}
              className="w-14 h-14 rounded-full bg-bargeham-600 text-white flex items-center justify-center hover:bg-bargeham-700">
              {playing ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-0.5" />}
            </button>
            <button onClick={() => skipChapter(1)} className="p-2 text-gray-600 hover:text-bargeham-600">
              <SkipForward className="w-6 h-6" />
            </button>
          </div>
          <div className="text-center text-sm text-gray-500 font-mono">
            {fmt(currentTime)} / {fmt(duration)}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-white p-1 rounded-lg border border-gray-200 w-fit">
          <button onClick={() => setTab("transcript")}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium ${tab === "transcript" ? "bg-bargeham-600 text-white" : "text-gray-600 hover:bg-gray-100"}`}>
            <FileText className="w-4 h-4" /> رونویسی ({segments.length})
          </button>
          <button onClick={() => setTab("chapters")}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium ${tab === "chapters" ? "bg-bargeham-600 text-white" : "text-gray-600 hover:bg-gray-100"}`}>
            <List className="w-4 h-4" /> فصل‌ها ({chapters.length})
          </button>
        </div>

        {/* Tab content */}
        <div className="bg-white p-5 rounded-lg border border-gray-200 min-h-[200px]">
          {tab === "transcript" && (
            segments.length === 0 ? (
              <div className="text-center py-10 text-gray-500">
                <FileText className="w-10 h-10 mx-auto mb-2 text-gray-300" />
                <p>رونویسی موجود نیست یا در حال پردازش است.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {segments.map((seg) => (
                  <button key={seg.id} onClick={() => seek(seg.start_seconds)}
                    className={`w-full text-right flex gap-3 p-2 rounded-lg hover:bg-bargeham-50 transition-colors ${Math.abs(currentTime - seg.start_seconds) < 2 ? "bg-bargeham-50" : ""}`}>
                    <span className="text-xs font-mono text-bargeham-600 shrink-0 pt-0.5">{fmt(seg.start_seconds)}</span>
                    <span className="text-sm text-gray-800 flex-1">{seg.text}</span>
                    {seg.speaker && <Badge variant="default">{seg.speaker}</Badge>}
                  </button>
                ))}
              </div>
            )
          )}

          {tab === "chapters" && (
            <div className="space-y-3">
              <div className="flex gap-2">
                <input type="text" placeholder="عنوان فصل جدید (در زمان فعلی)"
                  value={newChapterTitle} onChange={(e) => setNewChapterTitle(e.target.value)}
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-bargeham-500" />
                <button onClick={handleAddChapter} disabled={!newChapterTitle.trim()}
                  className="px-4 py-1.5 bg-bargeham-600 text-white rounded-lg text-sm hover:bg-bargeham-700 disabled:opacity-50">
                  افزودن
                </button>
              </div>
              {chapters.length === 0 ? (
                <p className="text-center text-gray-500 py-6 text-sm">فصلی تعریف نشده — در زمان دلخواه «افزودن» را بزنید.</p>
              ) : (
                <div className="space-y-1">
                  {[...chapters].sort((a, b) => a.start_seconds - b.start_seconds).map((ch) => (
                    <button key={ch.id} onClick={() => seek(ch.start_seconds)}
                      className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-bargeham-50 text-right">
                      <span className="text-xs font-mono text-bargeham-600">{fmt(ch.start_seconds)}</span>
                      <span className="text-sm text-gray-800 flex-1">{ch.title}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}