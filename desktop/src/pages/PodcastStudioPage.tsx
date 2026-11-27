import { useEffect, useState } from "react";
import { creationApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import EmptyState from "@/components/ui/EmptyState";
import Badge from "@/components/ui/Badge";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { Plus, Mic, Play, Clock, RefreshCw, Users, MessageSquare } from "lucide-react";

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

export default function PodcastStudioPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [voices, setVoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [speakers, setSpeakers] = useState<any[]>([]);
  const [segments, setSegments] = useState<any[]>([]);
  const [newSpeaker, setNewSpeaker] = useState({ name: "", voiceId: "" });
  const [newSegment, setNewSegment] = useState({ speakerId: "", text: "" });

  const load = async () => {
    setLoading(true);
    try {
      const [projs, vocs] = await Promise.all([
        creationApi.listPodcasts(),
        creationApi.listVoices(),
      ]);
      setProjects(projs);
      setVoices(vocs);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const loadDetail = async (id: string) => {
    setSelected(id);
    try {
      const [sp, seg] = await Promise.all([
        creationApi.listPodcastSpeakers(id),
        creationApi.listPodcastSegments(id),
      ]);
      setSpeakers(sp);
      setSegments(seg);
    } catch (err) { console.error(err); }
  };

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    try {
      await creationApi.createPodcast({ title: newTitle });
      setNewTitle("");
      setShowCreate(false);
      load();
    } catch (err: any) { alert("خطا: " + err.message); }
  };

  const handleAddSpeaker = async () => {
    if (!selected || !newSpeaker.name.trim() || !newSpeaker.voiceId) return;
    try {
      await creationApi.addPodcastSpeaker(selected, newSpeaker.name, newSpeaker.voiceId);
      setNewSpeaker({ name: "", voiceId: "" });
      loadDetail(selected);
    } catch (err: any) { alert("خطا: " + err.message); }
  };

  const handleAddSegment = async () => {
    if (!selected || !newSegment.text.trim()) return;
    try {
      await creationApi.addPodcastSegment(selected, {
        speaker_id: newSegment.speakerId || undefined,
        text: newSegment.text,
      });
      setNewSegment({ speakerId: "", text: "" });
      loadDetail(selected);
    } catch (err: any) { alert("خطا: " + err.message); }
  };

  const handleGenerate = async (id: string) => {
    try {
      await creationApi.generatePodcast(id);
      setTimeout(load, 1000);
    } catch (err: any) { alert("خطا: " + err.message); }
  };

  const currentProject = projects.find((p) => p.id === selected);

  return (
    <AppShell currentPath="#podcast">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Mic className="w-7 h-7 text-bargeham-600" />
              Podcast Studio
            </h1>
            <p className="text-gray-600 mt-1">ساخت پادکست چندگوینده با صداهای هوش مصنوعی</p>
          </div>
          <button onClick={() => setShowCreate(!showCreate)}
            className="flex items-center gap-2 px-4 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700">
            <Plus className="w-4 h-4" /> پادکست جدید
          </button>
        </div>

        {showCreate && (
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 flex gap-3">
            <input type="text" placeholder="عنوان پادکست..." value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-bargeham-500" />
            <button onClick={handleCreate} disabled={!newTitle.trim()}
              className="px-5 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700 disabled:opacity-50">
              ایجاد
            </button>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-20"><LoadingSpinner /></div>
        ) : projects.length === 0 ? (
          <EmptyState icon="🎙️" title="پادکستی ساخته نشده"
            subtitle="اولین پادکست چندگوینده خود را بسازید."
            actionText="ساخت پادکست" onAction={() => setShowCreate(true)} />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Project list */}
            <div className="lg:col-span-1 space-y-3">
              {projects.map((p) => {
                const st = STATUS[p.status] || { label: p.status, variant: "default" };
                return (
                  <button key={p.id} onClick={() => loadDetail(p.id)}
                    className={`w-full text-right p-4 rounded-lg border transition-colors ${
                      selected === p.id ? "border-bargeham-500 bg-bargeham-50" : "border-gray-200 bg-white hover:border-bargeham-300"
                    }`}>
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-medium text-gray-900 truncate">{p.title}</h3>
                      <Badge variant={st.variant}>{st.label}</Badge>
                    </div>
                    <div className="text-xs text-gray-500 flex items-center gap-2">
                      <Clock className="w-3 h-3" />{fmt(p.total_duration_seconds)}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Detail editor */}
            <div className="lg:col-span-2">
              {currentProject ? (
                <div className="bg-white p-6 rounded-lg border border-gray-200 space-y-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold text-gray-900">{currentProject.title}</h2>
                    {currentProject.status === "draft" && (
                      <button onClick={() => handleGenerate(currentProject.id)}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
                        <Play className="w-4 h-4" /> تولید پادکست
                      </button>
                    )}
                    {currentProject.status === "generating" && (
                      <span className="flex items-center gap-2 text-yellow-600 text-sm">
                        <RefreshCw className="w-4 h-4 animate-spin" /> در حال تولید...
                      </span>
                    )}
                  </div>

                  {/* Speakers */}
                  <div>
                    <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                      <Users className="w-4 h-4" /> گویندگان
                    </h3>
                    <div className="flex gap-2 mb-3">
                      <input type="text" placeholder="نام گوینده..." value={newSpeaker.name}
                        onChange={(e) => setNewSpeaker({ ...newSpeaker, name: e.target.value })}
                        className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm flex-1" />
                      <select value={newSpeaker.voiceId}
                        onChange={(e) => setNewSpeaker({ ...newSpeaker, voiceId: e.target.value })}
                        className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm flex-1">
                        <option value="">انتخاب صدا...</option>
                        {voices.map((v: any) => (
                          <option key={v.id} value={v.id}>{v.display_name}</option>
                        ))}
                      </select>
                      <button onClick={handleAddSpeaker} disabled={!newSpeaker.name.trim() || !newSpeaker.voiceId}
                        className="px-3 py-1.5 bg-bargeham-100 text-bargeham-700 rounded-lg text-sm disabled:opacity-50">
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {speakers.map((sp) => (
                        <Badge key={sp.id} variant="info">{sp.name}</Badge>
                      ))}
                    </div>
                  </div>

                  {/* Script segments */}
                  <div>
                    <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                      <MessageSquare className="w-4 h-4" /> اسکریپت
                    </h3>
                    <div className="space-y-2 mb-3 max-h-60 overflow-y-auto">
                      {segments.length === 0 ? (
                        <p className="text-sm text-gray-400 text-center py-4">هنوز متنی اضافه نشده</p>
                      ) : segments.map((seg, i) => (
                        <div key={seg.id} className="flex gap-2 p-2 bg-gray-50 rounded text-sm">
                          <span className="text-bargeham-600 font-mono shrink-0">{i + 1}.</span>
                          <span className="text-gray-800 flex-1">{seg.text}</span>
                        </div>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <select value={newSegment.speakerId}
                        onChange={(e) => setNewSegment({ ...newSegment, speakerId: e.target.value })}
                        className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm w-32">
                        <option value="">گوینده...</option>
                        {speakers.map((sp) => (
                          <option key={sp.id} value={sp.id}>{sp.name}</option>
                        ))}
                      </select>
                      <input type="text" placeholder="متن دیالوگ..." value={newSegment.text}
                        onChange={(e) => setNewSegment({ ...newSegment, text: e.target.value })}
                        onKeyDown={(e) => e.key === "Enter" && handleAddSegment()}
                        className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm flex-1" />
                      <button onClick={handleAddSegment} disabled={!newSegment.text.trim()}
                        className="px-3 py-1.5 bg-bargeham-100 text-bargeham-700 rounded-lg text-sm disabled:opacity-50">
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {currentProject.status === "ready" && currentProject.output_path && (
                    <div className="border-t pt-4">
                      <audio controls src={`http://localhost:8000/audio/${currentProject.id}/stream`} className="w-full" />
                    </div>
                  )}
                  {currentProject.status === "failed" && currentProject.error_message && (
                    <p className="text-xs text-red-500 bg-red-50 p-2 rounded">{currentProject.error_message}</p>
                  )}
                </div>
              ) : (
                <div className="bg-white p-10 rounded-lg border border-gray-200 text-center text-gray-400">
                  یک پادکست را برای ویرایش انتخاب کنید
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}