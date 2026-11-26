import { useState } from "react";
import { useStore } from "@/store/useStore";
import { api } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { setToken } = useStore();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await api.login(email, password);

      localStorage.setItem("bargeham_token", data.access_token);
      setToken(data.access_token);
      window.location.hash = "#dashboard";
    } catch (err: any) {
      setError(err.message || "ورود با خطا مواجه شد");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full items-center justify-center bg-gray-50">
      <div className="w-full max-w-md bg-white p-8 rounded-lg shadow border border-gray-200">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-10 h-10 bg-bargeham-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold">B</span>
          </div>
          <h1 className="text-xl font-bold text-gray-900">BARGEHAM</h1>
        </div>

        <h2 className="text-sm font-semibold text-gray-700 mb-6">ورود به سیستم</h2>

        {error && (
          <div className="mb-4 p-3 rounded bg-red-50 text-red-700 text-sm border border-red-100">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              پست الکترونیک
            </label>
            <input
              required
              type="email"
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-bargeham-500 focus:border-bargeham-500 outline-none"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              رمز عبور
            </label>
            <input
              required
              type="password"
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-bargeham-500 focus:border-bargeham-500 outline-none"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-bargeham-600 text-white py-2 rounded-lg font-medium hover:bg-bargeham-700 disabled:opacity-70 transition-colors"
          >
            {loading ? "در حال ورود..." : "ورود"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-600">
          کاربر mới؟{" "}
          <a
            href="#register"
            className="text-bargeham-600 hover:underline font-medium"
            onClick={(e) => {
              e.preventDefault();
              window.location.hash = "#register";
            }}
          >
            ثبت‌نام کنید
          </a>
        </p>
      </div>
    </div>
  );
}
