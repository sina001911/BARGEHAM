import { useEffect, useState } from "react";
import { academyApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import EmptyState from "@/components/ui/EmptyState";
import Badge from "@/components/ui/Badge";
import { BookOpen, Plus, GraduationCap, TrendingUp } from "lucide-react";

const COURSE_TYPE_LABELS: Record<string, string> = {
  personal: "شخصی",
  academic: "دانشگاهی",
  professional: "حرفه‌ای",
  language: "زبان",
  other: "سایر",
};

export default function AcademyPage() {
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");

  const loadCourses = async () => {
    try {
      const data = await academyApi.listCourses();
      setCourses(data);
    } catch (err) {
      console.error("Failed to load courses:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadCourses(); }, []);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      await academyApi.createCourse({ name: newName, description: newDesc || undefined });
      setNewName("");
      setNewDesc("");
      setShowCreate(false);
      loadCourses();
    } catch (err: any) {
      alert("خطا در ایجاد دوره: " + (err.message || "نامشخص"));
    }
  };

  const avgScore = courses.length > 0
    ? (courses.reduce((s, c) => s + (c.average_score || 0), 0) / courses.length * 100).toFixed(0)
    : "0";

  return (
    <AppShell currentPath="#academy">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <GraduationCap className="w-7 h-7 text-bargeham-600" />
              آکادمی BARGEHAM
            </h1>
            <p className="text-gray-600 mt-1">مدیریت دوره‌ها، درس‌ها و آزمون‌های هوشمند</p>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="flex items-center gap-2 px-4 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            دوره جدید
          </button>
        </div>

        {/* Stats bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "کل دوره‌ها", value: String(courses.length), icon: BookOpen, color: "bg-blue-100 text-blue-600" },
            { label: "میانگین نمرات", value: `${avgScore}%`, icon: TrendingUp, color: "bg-green-100 text-green-600" },
            { label: "درس‌های تولید شده", value: String(courses.reduce((s, c) => s + (c.lessons_completed || 0), 0)), icon: GraduationCap, color: "bg-purple-100 text-purple-600" },
            { label: "اسناد مرتبط", value: String(courses.reduce((s, c) => s + (c.documents_indexed || 0), 0)), icon: BookOpen, color: "bg-orange-100 text-orange-600" },
          ].map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label} className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <div className={`w-8 h-8 rounded-lg ${stat.color} flex items-center justify-center mb-2`}>
                  <Icon className="w-4 h-4" />
                </div>
                <p className="text-xl font-bold text-gray-900">{stat.value}</p>
                <p className="text-xs text-gray-500">{stat.label}</p>
              </div>
            );
          })}
        </div>

        {/* Create form */}
        {showCreate && (
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
            <h2 className="font-semibold text-gray-900">ایجاد دوره جدید</h2>
            <input
              type="text"
              placeholder="نام دوره..."
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-bargeham-500"
            />
            <textarea
              placeholder="توضیحات دوره (اختیاری)..."
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-bargeham-500"
            />
            <div className="flex gap-3">
              <button onClick={handleCreate} disabled={!newName.trim()}
                className="px-5 py-2 bg-bargeham-600 text-white rounded-lg font-medium hover:bg-bargeham-700 disabled:opacity-50">
                ایجاد
              </button>
              <button onClick={() => setShowCreate(false)}
                className="px-5 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50">
                انصراف
              </button>
            </div>
          </div>
        )}

        {/* Course list */}
        {loading ? (
          <div className="flex justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-bargeham-600"></div>
          </div>
        ) : courses.length === 0 ? (
          <EmptyState
            icon="🎓"
            title="هنوز دور‌ه‌ای ساخته نشده"
            subtitle="اولین دوره آکادمی خود را بسازید و اسناد مرتبط را به آن پیوند دهید."
            actionText="ایجاد اولین دوره"
            onAction={() => setShowCreate(true)}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses.map((course) => (
              <a
                key={course.id}
                href={`#academy/course/${course.id}`}
                onClick={(e) => { e.preventDefault(); window.location.hash = `#academy/course/${course.id}`; }}
                className="bg-white p-5 rounded-lg shadow-sm border border-gray-200 hover:shadow-md hover:border-bargeham-300 transition-all cursor-pointer"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-bold text-gray-900 text-lg truncate flex-1">{course.name}</h3>
                  <Badge variant="info">{COURSE_TYPE_LABELS[course.course_type] || course.course_type}</Badge>
                </div>
                {course.description && (
                  <p className="text-sm text-gray-600 line-clamp-2 mb-4">{course.description}</p>
                )}
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>{course.documents_indexed ?? 0} سند</span>
                  <span>{course.quizzes_taken ?? 0} آزمون</span>
                  <span className="text-green-600 font-medium">{Math.round((course.average_score ?? 0) * 100)}% میانگین</span>
                </div>
                <div className="mt-3 w-full bg-gray-100 rounded-full h-1.5">
                  <div
                    className="bg-bargeham-600 h-1.5 rounded-full"
                    style={{ width: `${Math.round((course.average_score ?? 0) * 100)}%` }}
                  />
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
