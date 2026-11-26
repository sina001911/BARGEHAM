const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Method = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

let token: string | null = null;

export function setAuthToken(t: string | null) {
  token = t;
}

async function request<T = unknown>(
  path: string,
  opts: {
    method?: Method;
    body?: unknown;
    headers?: Record<string, string>;
    query?: Record<string, string | number | boolean>;
  } = {}
): Promise<T> {
  const { method = "GET", body, headers, query } = opts;
  const url = new URL(`${BASE_URL}${path}`);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      url.searchParams.append(k, String(v));
    }
  }

  const init: RequestInit = {
    method,
    headers: {
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(body && method !== "GET"
        ? { "Content-Type": "application/json" }
        : {}),
      ...headers,
    },
  };
  if (body && method !== "GET") {
    init.body = JSON.stringify(body);
  }

  const res = await fetch(url.toString(), init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const json = await res.json();
      detail =
        (json as { message?: string; detail?: string })?.message ??
        (json as { message?: string; detail?: string })?.detail ??
        detail;
    } catch {
      // ignore non-JSON errors
    }
    throw new Error(`API ${res.status}: ${detail}`);
  }

  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) {
    return (await res.json()) as T;
  }
  return (await res.text()) as unknown as T;
}

export const api = {
  get: <T = unknown>(
    path: string,
    opts?: Parameters<typeof request>[1]
  ) => request<T>(path, { ...opts, method: "GET" }),
  post: <T = unknown>(
    path: string,
    body?: unknown,
    opts?: Parameters<typeof request>[1]
  ) => request<T>(path, { ...opts, method: "POST", body }),
  put: <T = unknown>(
    path: string,
    body?: unknown,
    opts?: Parameters<typeof request>[1]
  ) => request<T>(path, { ...opts, method: "PUT", body }),
  patch: <T = unknown>(
    path: string,
    body?: unknown,
    opts?: Parameters<typeof request>[1]
  ) => request<T>(path, { ...opts, method: "PATCH", body }),
  del: <T = unknown>(
    path: string,
    opts?: Parameters<typeof request>[1]
  ) => request<T>(path, { ...opts, method: "DELETE" }),
};
