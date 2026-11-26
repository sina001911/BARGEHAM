import { useEffect, useRef, useState } from "react";
import { academyApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { ArrowLeft, Send, Bot, User as UserIcon } from "lucide-react";

type Message = { role: "user" | "assistant"; content: string; mode?: string };

export default function SocraticPage() {
  const sessionId = typeof window !== "undefined" ? window.location.hash.match(/socratic\/([^/]+)/)?.[1] : null;
  const courseId = new URLSearchParams(typeof window !== "undefined" ? window.location.hash.split("?")[1] || "" : {}).get("course") || "";

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [topic, setTopic] = useState("");
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => { scrollToBottom(); }, [messages]);

  const loadOrCreateSession = async () => {
    setLoading(true);
    try {
      if (sessionId) {
        // Load existing session from SSE endpoint or stored messages
        const res = await fetch(`http://localhost:8000/academy/socratic/sessions/${sessionId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` },
        });
        if (res.ok) {
          const data = await res.json();
          setSession(data);
          setMessages((data.messages || []).map((m: any) => ({
            role: m.role || "assistant",
            content: m.content || "",
            mode: m.mode,
          })));
        }
      } else if (courseId && topic.trim()) {
        // Create new session
        const s = await academyApi.createSocraticSession(courseId, topic);
        setSession(s);
        setMessages([{ role: "assistant", content: s.greeting || `بیایید درباره "${topic}" گفت‌وگو کنیم. چه چیزی می‌دانید؟`, mode: "intro" }]);
      }
    } catch (err) {
      console.error("Failed to setup session:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadOrCreateSession(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSend = async () => {
    if (!input.trim() || sending || !session) return;
    const userMsg = input.trim();
    setInput("");
    setSending(true);
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);

    try {
      const resp = await academyApi.respondToSocratic(session.id, userMsg);
      if (resp.message) {
        setMessages((prev) => [...prev, {
          role: "assistant",
          content: resp.message,
          mode: resp.mode || "explanation",
        }]);
      }
    } catch (err: any) {
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: "خطا در دریافت پاسخ: " + (err.message || "نامشخص"),
      }]);
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return <AppShell currentPath="#academy"><div className="flex justify-center py-20"><LoadingSpinner /></div></AppShell>;
  }

  // Topic selection screen
  if (!session) {
    return (
      <AppShell currentPath="#academy">
        <div className="max-w-md mx-auto space-y-6 py-10">
          <button onClick={() => { window.location.hash = "#academy"; }}
            className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div className="text-center">
            <Bot className="w-12 h-12 text-bargeham-600 mx-auto mb-3" />
            <h1 className="text-2xl font-bold text-gray-900">گفت‌وگوی سقراطی</h1>
            <p className="text-gray-600 mt-2">موضوعی را انتخاب کنید تا با پرسش و پاسخ عمیق شخیص بینیم.</p>
          </div>
          <div className="bg-white p-5 rounded-lg border border-gray-200 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">موضوع گفت‌وگو</label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="مثلاً: فلسفه وجود دارد؟، اخلاق، هوش مصنوعی..."
                className="w-full border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-bargeham-500"
              />
            </div>
            <button
              onClick={() => { if (topic.trim()) loadOrCreateSession(); }}
              disabled={!topic.trim()}
              className="w-full py-3 bg-bargeham-600 text-white rounded-lg font-semibold hover:bg-bargeham-700 disabled:opacity-50"
            >
              شروع گفت‌وگو
            </button>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell currentPath="#academy">
      <div className="max-w-2xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
        {/* Header */}
        <div className="flex items-center gap-3 pb-4 border-b border-gray-200">
          <button onClick={() => { window.location.hash = "#academy"; }}
            className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div className="flex-1">
            <h1 className="font-bold text-gray-900">گفت‌وگوی سقراطی</h1>
            <p className="text-xs text-gray-500">{session?.topic || topic}</p>
          </div>
          <button onClick={async () => {
            await academyApi.closeSocraticSession(session.id);
            window.location.hash = "#academy";
          }}
            className="px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50">
            پایان
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 py-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex items-end gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-bargeham-100 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-bargeham-600" />
                </div>
              )}
              <div className={`max-w-[80%] p-3 rounded-2xl text-sm ${
                msg.role === "user"
                  ? "bg-bargeham-600 text-white rounded-br-sm"
                  : "bg-gray-100 text-gray-900 rounded-bl-sm"
              }`}>
                {msg.content}
                {msg.mode && msg.mode !== "explanation" && (
                  <span className={`text-xs block mt-1 ${msg.role === "user" ? "text-bargeham-200" : "text-gray-400"}`}>
                    {msg.mode === "question" ? "❓ پرسش" : msg.mode === "hint" ? "💡 راهنمایی" : msg.mode === "feedback" ? "✅ بازخورد" : ""}
                  </span>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0">
                  <UserIcon className="w-4 h-4 text-gray-600" />
                </div>
              )}
            </div>
          ))}
          {sending && (
            <div className="flex items-end gap-2">
              <div className="w-8 h-8 rounded-full bg-bargeham-100 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-bargeham-600" />
              </div>
              <div className="bg-gray-100 p-3 rounded-2xl rounded-bl-sm">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <form onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="flex gap-2 pt-4 border-t border-gray-200">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="پاسخ خود را بنویسید..."
            disabled={sending}
            className="flex-1 border border-gray-300 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-bargeham-500 disabled:opacity-50"
          />
          <button type="submit" disabled={sending || !input.trim()}
            className="px-4 bg-bargeham-600 text-white rounded-xl hover:bg-bargeham-700 disabled:opacity-50 transition-colors">
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </AppShell>
  );
}
