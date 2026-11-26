import React, { useState } from "react";
import { useStore } from "@/store/useStore";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { Settings, Bell, Language, Palette, Shield, User, LogOut } from "lucide-react";

export default function SettingsPage() {
  const { token, setToken } = useStore();
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [language, setLanguage] = useState<"fa" | "en">("fa");
  const [notifications, setNotifications] = useState(true);

  const handleLogout = () => {
    setToken(null);
    window.location.hash = "#login";
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">تنظیمات</h1>
        <p className="text-gray-600">تنظیمات شخصی و تلاشبری برنامه</p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="font-bold text-gray-900">'apparencia</h2>
        </div>
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-900">تم برنامه</h3>
              <p className="text-sm text-gray-500">انتخاب تم روشن یا تیره</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setTheme("light")}
                className={`px-3 py-1 rounded-md border ${theme === "light" ? "border-bargeham-600 bg-bargeham-50 text-bargeham-600" : "border-gray-200 text-gray-600 hover:bg-gray-50"}`}
              >
                روشن
              </button>
              <button
                onClick={() => setTheme("dark")}
                className={`px-3 py-1 rounded-md border ${theme === "dark" ? "border-bargeham-600 bg-bargeham-50 text-bargeham-600" : "border-gray-200 text-gray-600 hover:bg-gray-50"}`}
              >
                تیره
              </button>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-900">زبان</h3>
              <p className="text-sm text-gray-500">انتخاب زبان نمایش</p>
            </div>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as "fa" | "en")}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-bargeham-500 outline-none"
            >
              <option value="fa">فارسی</option>
              <option value="en">English</option>
            </select>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bell className="w-5 h-5 text-gray-500" />
              <div>
                <h3 className="font-medium text-gray-900">اعلان‌ها</h3>
                <p className="text-sm text-gray-500">دریافت اعلان‌های سیستم</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={notifications}
              onChange={(e) => setNotifications(e.target.checked)}
              className="w-4 h-4 rounded border-gray-300 text-bargeham-600 focus:ring-bargeham-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="font-bold text-gray-900">حساب کاربری</h2>
        </div>
        <div className="p-6 space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-bargeham-100 flex items-center justify-center">
              <User className="w-5 h-5 text-bargeham-600" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">کاربر فعلی</h3>
              <p className="text-sm text-gray-500">test@example.com</p>
            </div>
          </div>
          <div className="border-t pt-4">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg font-medium"
            >
              <LogOut className="w-4 h-4" />
              خروج از حساب
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="font-bold text-gray-900">درباره برنامه</h2>
        </div>
        <div className="p-6 space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">نسخه برنامه:</span>
            <span className="text-sm font-medium text-gray-900">0.1.0</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">موتور سرور:</span>
            <span className="text-sm font-medium text-gray-900">FastAPI</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">موتور وب:</span>
            <span className="text-sm font-medium text-gray-900">Tauri 2 + React</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">موتور OCR:</span>
            <span className="text-sm font-medium text-gray-900">PaddleOCR + Tesseract</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">پایگاه داده:</span>
            <span className="text-sm font-medium text-gray-900">PostgreSQL + pgvector</span>
          </div>
        </div>
      </div>
    </div>
  );
}
