"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

const nav = [
  { href: "/dashboard", label: "داشبورد" },
  { href: "/documents", label: "اسناد" },
  { href: "/upload", label: "بارگذاری" },
  { href: "/search", label: "جستجو" },
  { href: "/ask", label: "پرسش و پاسخ" },
];

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const pathname = usePathname();
  const router = useRouter();

  return (
    <nav className="border-b bg-white/95 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/dashboard" className="font-bold text-xl tracking-tight">
          BARGEHAM
        </Link>
        <div className="flex items-center gap-2">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`px-3 py-2 text-sm rounded-md transition ${
                pathname === item.href
                  ? "bg-blue-50 text-blue-600 font-medium"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              {item.label}
            </Link>
          ))}
          {user ? (
            <div className="ml-4 flex items-center gap-3 text-sm">
              <span className="text-gray-600">{user.full_name}</span>
              <button
                onClick={() => {
                  logout();
                  router.push("/login");
                }}
                className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-md"
              >
                خروج
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link href="/login" className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-md">
                ورود
              </Link>
              <Link href="/register" className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700">
                ثبت‌نام
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
