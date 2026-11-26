import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { api, setAuthToken } from "@/lib/api";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  role_id: string | null;
  role: {
    id: string;
    name: string;
    display_name: string;
  } | null;
  created_at: string;
  last_login: string | null;
}

interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface AuthState {
  user: User | null;
  token: Token | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    fullName: string,
    password: string
  ) => Promise<void>;
  logout: () => void;
  setToken: (t: Token | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      setToken: (t) => {
        set({ token: t, isAuthenticated: !!t });
        setAuthToken(t?.access_token ?? null);
      },

      login: async (email, password) => {
        const res = await api.post<Token>("/auth/login", { email, password });
        set({ token: res, user: null, isAuthenticated: true });
        setAuthToken(res.access_token);
      },

      register: async (email, fullName, password) => {
        await api.post<Token>("/auth/register", {
          email,
          full_name: fullName,
          password,
        });
      },

      logout: () => {
        set({ user: null, token: null, isAuthenticated: false });
        setAuthToken(null);
        if (typeof window !== "undefined") {
          localStorage.removeItem("auth-storage");
        }
      },
    }),
    {
      name: "auth-storage",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ token: state.token }),
    }
  )
);
