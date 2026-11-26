import React, { useEffect, useState } from "react";
import { listen } from "@tauri-apps/api/event";
import { api, notify } from "@/lib/api";
import { useStore } from "@/store/useStore";
import AppShell from "@/components/layout/AppShell";
import DashboardPage from "@/pages/DashboardPage";
import DocumentsPage from "@/pages/DocumentsPage";
import UploadPage from "@/pages/UploadPage";
import SearchPage from "@/pages/SearchPage";
import AskPage from "@/pages/AskPage";
import DocumentDetailPage from "@/pages/DocumentDetailPage";
import SettingsPage from "@/pages/SettingsPage";
import AcademyPage from "@/pages/AcademyPage";
import CourseDetailPage from "@/pages/CourseDetailPage";
import QuizPage from "@/pages/QuizPage";
import FlashcardsPage from "@/pages/FlashcardsPage";
import SocraticPage from "@/pages/SocraticPage";
import AudioLibraryPage from "@/pages/AudioLibraryPage";
import AudioPlayerPage from "@/pages/AudioPlayerPage";
import Toast from "@/components/ui/Toast";

const PAGE_ROUTES: Record<string, React.ComponentType> = {
  dashboard: DashboardPage,
  documents: DocumentsPage,
  upload: UploadPage,
  search: SearchPage,
  ask: AskPage,
  settings: SettingsPage,
};

// Academy pages wrap themselves in AppShell, so they render standalone.
const SELF_WRAPPED_ROUTES = new Set([
  "academy",
  "academy-course",
  "academy-quiz",
  "academy-flashcards",
  "academy-socratic",
  "audio",
  "audio-player",
]);

export default function App() {
  const [initialized, setInitialized] = useState(false);
  const [hash, setHash] = useState(window.location.hash.slice(1) || "dashboard");
  const [docId, setDocId] = useState<string | null>(null);

  useEffect(() => {
    const init = async () => {
      try {
        const online = await api.checkBackendHealth();
        const { setBackendOnline } = useStore.getState();
        setBackendOnline(online);
      } catch {
        const { setBackendOnline } = useStore.getState();
        setBackendOnline(false);
      }
      setInitialized(true);
    };
    init();
  }, []);

  useEffect(() => {
    const handler = () => {
      const h = window.location.hash.slice(1);
      const docMatch = h.match(/^documents\/(.+)$/);
      if (docMatch) {
        setHash("document");
        setDocId(docMatch[1]);
        return;
      }
      // Academy sub-routes
      if (h.startsWith("academy/course/")) {
        setHash("academy-course");
        return;
      }
      if (h.startsWith("academy/quiz/")) {
        setHash("academy-quiz");
        return;
      }
      if (h.startsWith("academy/flashcards")) {
        setHash("academy-flashcards");
        return;
      }
      if (h.startsWith("academy/socratic")) {
        setHash("academy-socratic");
        return;
      }
      if (h.startsWith("audio/player/")) {
        setHash("audio-player");
        return;
      }
      setHash(h || "dashboard");
      setDocId(null);
    };
    window.addEventListener("hashchange", handler);
    const h = window.location.hash.slice(1);
    const docMatch = h.match(/^documents\/(.+)$/);
    if (docMatch) {
      setHash("document");
      setDocId(docMatch[1]);
    } else if (h.startsWith("academy/course/")) {
      setHash("academy-course");
    } else if (h.startsWith("academy/quiz/")) {
      setHash("academy-quiz");
    } else if (h.startsWith("academy/flashcards")) {
      setHash("academy-flashcards");
    } else if (h.startsWith("academy/socratic")) {
      setHash("academy-socratic");
    } else if (h.startsWith("audio/player/")) {
      setHash("audio-player");
    } else {
      setHash(h || "dashboard");
    }
    return () => window.removeEventListener("hashchange", handler);
  }, []);

  useEffect(() => {
    const unlisten = listen("document-uploaded", async (event: any) => {
      const payload = event.payload;
      if (payload && payload.document_id) {
        const { fetchDocuments } = useStore.getState();
        await fetchDocuments();
        notify.success("سند بارگذاری شد", "سند جدید با موفقیت بارگذاری و در حال پردازش است");
      }
    });
    return () => {
      unlisten.then((u) => u());
    };
  }, []);

  useEffect(() => {
    const unlisten = listen("file-changed", (event: any) => {
      const payload = event.payload;
      if (payload && payload.path) {
        console.log("File changed:", payload.path);
      }
    });
    return () => {
      unlisten.then((u) => u());
    };
  }, []);

  if (!initialized) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-bargeham-600"></div>
          <p className="text-gray-600">در حال بارگذاری...</p>
        </div>
      </div>
    );
  }

  // Academy pages manage their own AppShell wrapper.
  if (SELF_WRAPPED_ROUTES.has(hash)) {
    return (
      <>
        <Toast />
        {hash === "academy" && <AcademyPage />}
        {hash === "academy-course" && <CourseDetailPage />}
        {hash === "academy-quiz" && <QuizPage />}
        {hash === "academy-flashcards" && <FlashcardsPage />}
        {hash === "academy-socratic" && <SocraticPage />}
        {hash === "audio" && <AudioLibraryPage />}
        {hash === "audio-player" && <AudioPlayerPage />}
      </>
    );
  }

  const PageComponent = PAGE_ROUTES[hash] || DashboardPage;

  return (
    <AppShell currentPath={`#${hash}`}>
      <Toast />
      {hash === "document" && docId ? (
        <DocumentDetailPage documentId={docId} />
      ) : (
        <PageComponent />
      )}
    </AppShell>
  );
}
