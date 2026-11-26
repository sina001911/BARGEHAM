import { useEffect, useState, type ReactNode } from "react";
import { academyApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import EmptyState from "@/components/ui/EmptyState";
import Badge from "@/components/ui/Badge";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { ArrowLeft, BookOpen, FileText, Brain, Play, Trash2 } from "lucide-react";

type Tab = "lessons" | "quizzes" | "flashcards";

export default function CourseDetailPage() {
  const courseId = typeof window !== "undefined" ? window.location.hash.match(/course\/([^/]+)/)?.[1] : null;
  const [course, setCourse] = useState<any>(null);
  const [lessons, setLessons] = useState<any[]>([]);
  const [quizzes, setQuizzes] = useState<any[]>([]);
  const [flashcards, setFlashcards] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>("lessons");
  const [generating, setGenerating] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    if (!courseId) return;
    setLoading(true);
    try {
      const [c, l, q, f] = await Promise.all([
        academyApi.getCourse(courseId),
        academyApi.listLessons(courseId),
        academyApi.listQuizzes(courseId),
        academyApi.listFlashcards(courseId),
      ]);
      setCourse(c);
      setLessons(l);
      setQuizzes(q);
      setFlashcards(f);
    } catch (err) {
      console.error("Failed to load course:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [courseId]);

  const handleGenerateLesson = async (topic: string) => {
    if (!topic.trim() || !courseId) return;
    setGenerating(topic);
    try {
      const lesson = await academyApi.generateLesson(courseId, topic);
      setLessons((prev) => [...prev, lesson]);
    } catch (err: any) {
      alert("خطا در تولید درس: " + (err.message || "نامشخص"));
    } finally {
      setGenerating(null);
    }
  };

  const handleDeleteLesson = async (lessonId: string) => {
    if (!confirm("آیا از حذف این درس اطمینان دارید؟")) return;
    try {
      await academyApi.deleteLesson(lessonId);
      setLessons((prev) => prev.filter((l) => l.id !== lessonId));
    } catch (err: any) {
      alert("خطا: " + (err.message || "نامشعرف"));
    }
  };

  const handleGenerateQuiz = async () => {
    if (!courseId) return;
    setGenerating("quiz");
    try {
      const quiz = await academyApi.generateQuiz(courseId, 10);
      setQuizzes((prev) => [...prev, quiz]);
    } catch (err: any) {
      alert("خطا: " + (err.message || "نامشخص"));
    } finally {
      setGenerating(null);
    }
  };

  const tabItems: { key: Tab; label: string; icon: ReactNode; count: number }[] = [
    { key: "lessons", label: "درس‌ها", icon: <BookOpen className="w-4 h-4" />, count: lessons.length },
    { key: "quizzes", label: "آزمون‌ها", icon: <Play className="w-4 h-4" />, count: quizzes.length },
    { key: "flashcards", label: "فلش‌کارت", icon: <Brain className="w-4 h-4" />, count: flashcards.length },
  ];

  if (loading) {
    return <AppShell currentPath="#academy"><div className="flex justify-center py-20"><LoadingSpinner /></div></AppShell>;
  }

  if (!course) {
    return (
      <AppShell currentPath="#academy">
        <EmptyState icon="🔍" title="دوره یافت نشد" subtitle="دوره مورد نظر وجود ندارد یا حذف شده است."
          actionText="بازگشت" onAction={() => { window.location.hash = "#academy"; }} />
      </AppShell>
    );
  }

  return (
    <AppShell currentPath="#academy">
      <div className="space-y-6">
        {/* Back + header */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => { window.location.hash = "#academy"; }}
            className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{course.name}</h1>
            {course.description && (
              <p className="text-gray-600 mt-1">{course.description}</p>
            )}
          </div>
          <div className="ml-auto flex gap-2">
            <Badge variant="info">{course.course_type || "personal"}</Badge>
          </div>
        </div>

        {/* Progress stats */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "اسناد مرتبط", value: course.documents_indexed ?? 0, icon: FileText },
            { label: "بخش‌های ايندكس شده", value: course.chunks_indexed ?? 0, icon: BookOpen },
            { label: "درس‌هاي تکميل شده", value: course.lessons_completed ?? 0, icon: Play },
            { label: "میانگين نمرات", value: `${Math.round((course.average_score ?? 0) * 100)}%`, icon: Brain },
          ].map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label} className="bg-white p-4 rounded-lg border border-gray-200 text-center">
                <Icon className="w-5 h-5 text-bargeham-600 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                <p className="text-xs text-gray-500">{stat.label}</p>
              </div>
            );
          })}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-white p-1 rounded-lg border border-gray-200 w-fit">
          {tabItems.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "bg-bargeham-600 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
              <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                activeTab === tab.key ? "bg-white/20" : "bg-gray-100"
              }`}>{tab.count}</span>
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 min-h-[300px]">
          {activeTab === "lessons" && (
            <>
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-900">درس‌ها ({lessons.length})</h2>
                <button
                  onClick={() => handleGenerateLesson(prompt("موضوع درس جدید:") || "")}
                  disabled={!!generating}
                  className="flex items-center gap-2 px-4 py-2 bg-bargeham-600 text-white rounded-lg text-sm hover:bg-bargeham-700 disabled:opacity-50"
                >
                  <PlusIcon className="w-4 h-4" />
                  تولید درس جدید
                </button>
              </div>
              {lessons.length === 0 ? (
                <EmptyState icon="📖" title="هنوز درسی ساخته نشده" subtitle="با وارد کردن موضوع، درس هوشمند تولید کنید."
                  actionText="توليد درس" onAction={() => handleGenerateLesson(prompt("موضوع:") || "")} />
              ) : (
                <div className="space-y-3">
                  {lessons.map((lesson) => (
                    <div key={lesson.id} className="flex items-center gap-4 p-4 rounded-lg border border-gray-100 hover:border-bargeham-200 transition-colors">
                      <div className="w-10 h-10 rounded-lg bg-bargeham-50 flex items-center justify-center text-bargeham-600 font-bold text-sm">
                        {lesson.order_index ?? "-"}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 truncate">{lesson.title || lesson.topic}</div>
                        <div className="text-sm text-gray-500 flex items-center gap-3 mt-0.5">
                          <span>{lesson.lesson_type || "concept"}</span>
                          {lesson.estimated_minutes && <span>· {lesson.estimated_minutes} دقیقه</span>}
                        </div>
                      </div>
                      <Badge variant={lesson.status === "published" ? "success" : "warning"}>
                        {lesson.status === "published" ? "منتشر شده" : "پیش‌نویس"}
                      </Badge>
                      <button onClick={() => handleDeleteLesson(lesson.id)}
                        className="p-2 text-gray-400 hover:text-red-500 transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {activeTab === "quizzes" && (
            <>
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-900">آزمون‌ها ({quizzes.length})</h2>
                <button
                  onClick={handleGenerateQuiz}
                  disabled={!!generating}
                  className="flex items-center gap-2 px-4 py-2 bg-bargeham-600 text-white rounded-lg text-sm hover:bg-bargeham-700 disabled:opacity-50"
                >
                  <PlusIcon className="w-4 h-4" />
                  ساخت آزمون
                </button>
              </div>
              {quizzes.length === 0 ? (
                <EmptyState icon="❓" title="هنوز آزمونی نیست" subtitle="یک آزمون هوشمند بر اساس محتوای دوره بسازید."
                  actionText="ساخت آزمون" onAction={handleGenerateQuiz} />
              ) : (
                <div className="space-y-3">
                  {quizzes.map((q) => (
                    <div key={q.id} className="p-4 rounded-lg border border-gray-100 hover:border-bargeham-200 transition-colors">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-gray-900">{q.title || "آزمون بدون عنوان"}</div>
                          <div className="text-sm text-gray-500 mt-1">{q.quiz_type || "multiple_choice"}</div>
                        </div>
                        <button
                          onClick={() => { window.location.hash = `#academy/quiz/${q.id}`; }}
                          className="px-4 py-2 bg-bargeham-100 text-bargeham-700 rounded-lg text-sm font-medium hover:bg-bargeham-200"
                        >
                          شروع آزمون
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {activeTab === "flashcards" && (
            <>
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-900">فلش‌کارت‌ها ({flashcards.length})</h2>
                <a href={`#academy/flashcards?course=${courseId}`}
                  className="px-4 py-2 bg-bargeham-600 text-white rounded-lg text-sm hover:bg-bargeham-700">
                  مرور فلش‌کارت‌ها
                </a>
              </div>
              {flashcards.length === 0 ? (
                <EmptyState icon="🗂️" title="فلش‌کارتی وجود ندارد" subtitle="فلش‌کارت‌ها می‌توانند به صورت دستی یا خودکار از درس‌ها ساخته شوند."
                  actionText="مرور فلش‌کارت‌ها" onAction={() => { window.location.hash = `#academy/flashcards?course=${courseId}`; }} />
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {flashcards.slice(0, 8).map((card) => (
                    <div key={card.id} className="p-4 rounded-lg border border-gray-100 bg-gradient-to-br from-gray-50 to-white">
                      <div className="text-sm font-medium text-gray-900 mb-1">{card.front?.substring(0, 80)}</div>
                      <div className="text-xs text-gray-500">پاسخ: {card.back?.substring(0, 80)}</div>
                      {card.interval_days != null && (
                        <div className="mt-2 text-xs text-bargeham-600">فاصله بعدی: {card.interval_days} روز</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </AppShell>
  );
}

function PlusIcon({ className }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>;
}
