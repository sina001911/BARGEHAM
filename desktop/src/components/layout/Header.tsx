import { useState } from "react";
import { Bell, Search, User, Settings } from "lucide-react";
import { useStore } from "@/store/useStore";

export function Header() {
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const { token, setToken } = useStore();

  const handleLogout = () => {
    setToken(null);
    window.location.hash = "#login";
  };

  return (
    <header className="sticky top-0 z-10 bg-white border-b border-gray-200">
      <div className="flex flex-row-reverse items-center justify-between px-6 py-3">
        {/* Right side (RTL end): search + auth */}
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2">
            <div className="relative">
              <Search className="w-4 h-4 absolute right-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder="جستجو در اسناد..."
                className="w-64 pr-10 pl-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bargeham-500 focus:border-bargeham-500 outline-none text-right"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              className="p-2 rounded-md text-gray-600 hover:bg-gray-100 relative"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 left-1 w-2 h-2 bg-red-500 rounded-full" />
            </button>

            {token ? (
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="p-2 rounded-md text-gray-600 hover:bg-gray-100 relative flex items-center gap-2"
              >
                <div className="w-8 h-8 rounded-full bg-bargeham-100 flex items-center justify-center">
                  <User className="w-4 h-4 text-bargeham-600" />
                </div>
                <span className="hidden sm:block text-sm font-medium text-gray-900">
                  کاربر
                </span>
                <svg
                  className="w-4 h-4 mr-1 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>
            ) : (
              <>
                <button
                  onClick={() => {
                    window.location.hash = "#register";
                  }}
                  className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  ثبت‌نام
                </button>
                <button
                  onClick={() => {
                    window.location.hash = "#login";
                  }}
                  className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
                >
                  ورود
                </button>
              </>
            )}
          </div>
        </div>

        {/* Left side (RTL start): brand + mobile menu */}
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold text-gray-900">BARGEHAM</h1>
          <button
            className="lg:hidden p-2 rounded-md text-gray-600 hover:bg-gray-100"
          >
            <MenuIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {token && userMenuOpen && (
        <div className="absolute left-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-2 z-50">
          <button
            className="flex w-full items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
          >
            <User className="w-4 h-4" />
            پروفایل
          </button>
          <button
            className="flex w-full items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
          >
            <Settings className="w-4 h-4" />
            تنظیمات
          </button>
          <hr className="my-1 border-gray-100" />
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
          >
            <LogOut className="w-4 h-4" />
            خروج از سیستم
          </button>
        </div>
      )}
    </header>
  );
}

function MenuIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 6h16M4 12h16M4 18h16"
      />
    </svg>
  );
}

function LogOut({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M17 16l4-4m0 0l-4-4m4 4H7"
      />
    </svg>
  );
}
