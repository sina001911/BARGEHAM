import { useEffect } from "react";
import { useStore } from "@/store/useStore";
import { api } from "@/lib/api";
import {
  FileText,
  Upload,
  Search,
  MessageCircle,
  Clock,
  CheckCircle,
} from "lucide-react";

const statCards = [
  {
    title: "مجموع اسناد",
    value: "0",
    icon: FileText,
    color: "bg-blue-100 text-blue-600",
  },
  {
    title: "در حال پردازش",
    value: "0",
    icon: Clock,
    color: "bg-yellow-100 text-yellow-600",
  },
  {
    title: "آماده",
    value: "0",
    icon: CheckCircle,
    color: "bg-green-100 text-green-600",
  },
  {
    title: "جستجوی هوشمند",
    value: "فعال",
    icon: Search,
    color: "bg-blue-100 text-blue-600",
  },
];

export default function DashboardPage() {
  const { documents, setDocuments, fetchDocuments } = useStore();

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">داشبورد</h1>
        <p className="text-gray-600">
          مدیریت، پردازش و استخراج دانش از اسناد — فارسی و انگلیسی
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.title} className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
              <div className={`w-10 h-10 rounded-lg ${card.color} flex items-center justify-center mb-3`}>
                <Icon className="w-5 h-5" />
              </div>
              <p className="text-2xl font-bold text-gray-900">{card.value}</p>
              <p className="text-sm text-gray-600">{card.title}</p>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-bold text-gray-900 mb-4">اسناد اخیر</h2>
          {documents.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <span className="text-gray-400">📄</span>
              <p className="mt-2">سندی ثبت نشده است</p>
              <a
                href="#upload"
                onClick={(e) => {
                  e.preventDefault();
                  window.location.hash = "#upload";
                }}
                className="mt-3 text-sm text-bargeham-600 hover:underline"
              >
                بارگذاری سند اول
              </a>
            </div>
          ) : (
            <ul className="space-y-3">
              {documents.slice(0, 5).map((doc) => (
                <li key={doc.id} className="flex items-center gap-3 p-2 rounded hover:bg-gray-50">
                  <div className="w-8 h-8 rounded bg-gray-100 flex items-center justify-center text-sm text-gray-600">
                    📄
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {doc.title || doc.file_name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {doc.file_name} · {doc.status}
                    </div>
                  </div>
                  <span className="text-xs px-2 py-1 rounded bg-green-100 text-green-700">
                    آماده
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-bold text-gray-900 mb-4">اقدامات سریع</h2>
          <div className="space-y-3">
            <a
              href="#upload"
              onClick={(e) => {
                e.preventDefault();
                window.location.hash = "#upload";
              }}
              className="flex items-center gap-3 px-4 py-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <Upload className="w-5 h-5 text-bargeham-600" />
              <span className="text-sm text-gray-900">بارگذاری سند جدید</span>
            </a>
            <a
              href="#search"
              onClick={(e) => {
                e.preventDefault();
                window.location.hash = "#search";
              }}
              className="flex items-center gap-3 px-4 py-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <Search className="w-5 h-5 text-bargeham-600" />
              <span className="text-sm text-gray-900">جستجو در اسناد</span>
            </a>
            <a
              href="#ask"
              onClick={(e) => {
                e.preventDefault();
                window.location.hash = "#ask";
              }}
              className="flex items-center gap-3 px-4 py-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <MessageCircle className="w-5 h-5 text-bargeham-600" />
              <span className="text-sm text-gray-900">پرسش از هوش مصنوعی</span>
            </a>
          </div>
        </div>

        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-bold text-gray-900 mb-4">آمار سیستم</h2>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">اسناد_INDEXED</span>
              <span className="text-sm font-medium text-gray-900">
                {documents.length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">فولدرهای_indexed</span>
              <span className="text-sm font-medium text-gray-900">0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">آخرین به‌روزرسانی</span>
              <span className="text-sm font-medium text-gray-900">اکنون</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
