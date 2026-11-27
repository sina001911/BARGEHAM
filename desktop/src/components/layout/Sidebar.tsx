import { useState } from "react";
import { LayoutDashboard, FileText, Upload, Search, MessageCircle, Settings, GraduationCap, Music, BookOpen, Mic, LogOut, Menu, X } from "lucide-react";

const navItems = [
  { href: "#dashboard", label: "داشبورد", icon: LayoutDashboard },
  { href: "#documents", label: "اسناد", icon: FileText },
  { href: "#upload", label: "بارگذاری", icon: Upload },
  { href: "#search", label: "جستجو", icon: Search },
  { href: "#ask", label: "پرسش و پاسخ", icon: MessageCircle },
  { href: "#academy", label: "آکادمی", icon: GraduationCap },
  { href: "#audio", label: "کتابخانه صوتی", icon: Music },
  { href: "#audiobook", label: "Audiobook Builder", icon: BookOpen },
  { href: "#podcast", label: "Podcast Studio", icon: Mic },
  { href: "#settings", label: "تنظیمات", icon: Settings },
];

export function Sidebar({ currentPath }: { currentPath: string }) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <>
      <aside className={`hidden lg:flex flex-col w-72 bg-white border-r border-gray-200 z-20`}>
        <div className="flex items-center gap-2 p-6 border-b border-gray-200">
          <div className="w-8 h-8 bg-bargeham-600 rounded-lg flex items-center justify-center">
            <FileText className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-gray-900">BARGEHAM</span>
        </div>

        <nav className="flex-1 px-4 py-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPath === item.href;
            return (
              <a
                key={item.href}
                href={item.href}
                onClick={(e) => {
                  e.preventDefault();
                  window.location.hash = item.href;
                }}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-bargeham-50 text-bargeham-600"
                    : "text-gray-600 hover:bg-gray-100 hover:text-bargeham-600"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </a>
            );
          })}
        </nav>

        <div className="p-4 border-t border-gray-200">
          <button
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>خروج از سیستم</span>
          </button>
        </div>
      </aside>

      {/* Mobile sidebar overlay */}
      <div className={`lg:hidden fixed inset-0 z-40 transition-all duration-300 ${
        isOpen ? "" : "hidden"
      }`}>
        <div className="absolute inset-0 bg-black opacity-50" onClick={() => setIsOpen(false)} />
        <div
          className={
            "absolute right-0 top-0 h-full w-72 bg-white border-l border-gray-200 shadow-2xl transform transition-transform duration-300 " +
            (isOpen ? "translate-x-0" : "translate-x-full")
          }
        >
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <span className="text-xl font-bold text-gray-900">BARGEHAM</span>
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 rounded-md text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <nav className="flex-1 px-4 py-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPath === item.href;
              return (
                <a
                  key={item.href}
                  href={item.href}
                  onClick={(e) => {
                    e.preventDefault();
                    window.location.hash = item.href;
                    setIsOpen(false);
                  }}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-bargeham-50 text-bargeham-600"
                      : "text-gray-600 hover:bg-gray-100 hover:text-bargeham-600"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </a>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Mobile menu button */}
      <button
        className="lg:hidden fixed bottom-6 left-6 z-50 bg-bargeham-600 text-white p-3 rounded-full shadow-lg flex items-center justify-center"
        onClick={() => setIsOpen(true)}
      >
        <Menu className="w-5 h-5" />
      </button>
    </>
  );
}
