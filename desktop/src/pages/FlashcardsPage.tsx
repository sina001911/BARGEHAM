import { useEffect, useState } from "react";
import { academyApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { ArrowLeft, Check, X } from "lucide-react";

export default function FlashcardsPage() {
  const params = new URLSearchParams(typeof window !== "undefined" ? window.location.hash.split("?")[1] || "" : "");
  const courseId = params.get("course") || "";
  const [flashcards, setFlashcards] = useState<any[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [, setReviewed] = useState(0);

  const loadCards = async () => {
    if (!courseId) return;
    setLoading(true);
    try {
      const cards = await academyApi.listFlashcards(courseId);
      // Sort by due_date (nulls last)
      const sorted = [...cards].sort((a, b) => {
        if (!a.due_date) return 1;
        if (!b.due_date) return -1;
        return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
      });
      setFlashcards(sorted);
    } catch (err) {
      console.error("Failed to load flashcards:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadCards(); }, [courseId]);

  const handleFlip = () => setFlipped((f) => !f);

  const handleReview = async (known: boolean) => {
    if (flashcards.length === 0) return;
    const card = flashcards[currentIndex];
    try {
      await academyApi.reviewFlashcard(card.id, known);
    } catch { /* ignore */ }
    setReviewed((r) => r + 1);
    setFlipped(false);
    if (currentIndex < flashcards.length - 1) {
      setCurrentIndex((i) => i + 1);
    } else {
      // All done — reload
      await loadCards();
      setCurrentIndex(0);
      setReviewed(0);
    }
  };

  if (loading) {
    return <AppShell currentPath="#academy"><div className="flex justify-center py-20"><LoadingSpinner /></div></AppShell>;
  }

  if (flashcards.length === 0) {
    return (
      <AppShell currentPath="#academy">
        <div className="flex flex-col items-center justify-center py-20 text-gray-500">
          <span className="text-5xl mb-4">🗂️</span>
          <p className="text-lg font-medium">فلش‌کارتی برای مرور وجود ندارد</p>
          <button onClick={() => { window.location.hash = "#academy"; }}
            className="mt-4 px-4 py-2 bg-bargeham-600 text-white rounded-lg hover:bg-bargeham-700">
            بازگشت
          </button>
        </div>
      </AppShell>
    );
  }

  const card = flashcards[currentIndex];
  const progressPct = Math.round((currentIndex / flashcards.length) * 100);

  return (
    <AppShell currentPath="#academy">
      <div className="max-w-xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button onClick={() => { window.location.hash = "#academy"; }}
            className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-gray-900">مرور فلش‌کارت‌ها</h1>
            <p className="text-sm text-gray-500">کارت {currentIndex + 1} از {flashcards.length}</p>
          </div>
        </div>

        {/* Progress */}
        <div className="w-full bg-gray-100 rounded-full h-2">
          <div className="bg-bargeham-600 h-2 rounded-full transition-all" style={{ width: `${progressPct}%` }} />
        </div>

        {/* Card */}
        <div
          onClick={handleFlip}
          className="cursor-pointer perspective-1000"
        >
          <div className={`relative w-full min-h-[280px] rounded-2xl shadow-lg border transition-all duration-300 flex flex-col items-center justify-center p-8 ${
            flipped ? "bg-bargeham-600 border-bargeham-600" : "bg-white border-gray-200"
          }`}>
            <p className={`text-center text-lg font-medium ${
              flipped ? "text-white" : "text-gray-900"
            }`}>
              {flipped ? card.back : card.front}
            </p>
            <p className={`text-xs mt-6 ${flipped ? "text-bargeham-200" : "text-gray-400"}`}>
              {flipped ? "برای بازگشت کلیک کنید" : "برای دیدن پاسخ کلیک کنید"}
            </p>
          </div>
        </div>

        {/* Review buttons */}
        {flipped && (
          <div className="flex gap-4">
            <button
              onClick={() => handleReview(false)}
              className="flex-1 flex items-center justify-center gap-2 py-3 border-2 border-red-300 text-red-600 rounded-xl font-medium hover:bg-red-50 transition-colors"
            >
              <X className="w-5 h-5" />
              نمی‌دانستم
            </button>
            <button
              onClick={() => handleReview(true)}
              className="flex-1 flex items-center justify-center gap-2 py-3 border-2 border-green-300 text-green-600 rounded-xl font-medium hover:bg-green-50 transition-colors"
            >
              <Check className="w-5 h-5" />
              می‌دانستم
            </button>
          </div>
        )}

        {/* Nav arrows when not flipped */}
        {!flipped && currentIndex > 0 && (
          <button onClick={() => { setFlipped(false); setCurrentIndex((i) => i - 1); }}
            className="w-full py-2 text-sm text-gray-500 hover:text-gray-700 border border-gray-200 rounded-lg">
            ← کارت قبلی
          </button>
        )}
      </div>
    </AppShell>
  );
}
