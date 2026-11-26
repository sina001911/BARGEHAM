import {
  open as openDialog,
  save as saveDialog,
} from "@tauri-apps/plugin-dialog";
import { sendNotification } from "@tauri-apps/plugin-notification";
import { open } from "@tauri-apps/plugin-shell";
import type {
  DocumentMetadata,
  UploadDocumentRequest,
  ListDocumentsRequest,
  DocumentListResponse,
  SearchRequest,
  SearchResult,
  AskRequest,
  AppConfig,
  FolderInfo,
  FolderCreate,
  TagRead,
  TagCreate,
} from "@/types";

const API_BASE = "http://localhost:8000";

// ---------------------------------------------------------------------------
// Backend HTTP API (direct fetch — no Tauri stubs)
// ---------------------------------------------------------------------------

async function request<T>(
  path: string,
  opts: {
    method?: string;
    body?: unknown;
    headers?: Record<string, string>;
    query?: Record<string, string | number | boolean | undefined>;
  } = {}
): Promise<T> {
  const { method = "GET", body, headers, query } = opts;
  const url = new URL(`${API_BASE}${path}`);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null) {
        url.searchParams.append(k, String(v));
      }
    }
  }

  const init: RequestInit = {
    method,
    headers: {
      Accept: "application/json",
      ...(body && method !== "GET" ? { "Content-Type": "application/json" } : {}),
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

async function requestFormData(path: string, formData: FormData): Promise<unknown> {
  const url = new URL(`${API_BASE}${path}`);
  const res = await fetch(url.toString(), {
    method: "POST",
    body: formData,
    headers: {
      Accept: "application/json",
    },
  });
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
  return res.json();
}

export const api = {
  // Config
  getConfig: async (): Promise<AppConfig> => {
    try {
      return await request<AppConfig>("/");
    } catch {
      return {
        api_base_url: API_BASE,
        max_upload_size_mb: 100,
        allowed_mime_types: [
          "application/pdf",
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          "text/plain",
          "image/png",
          "image/jpeg",
          "image/tiff",
          "image/webp",
        ],
        ocr_engine: "paddleocr",
        embedding_model: "sentence-transformers/paraphrase-MultiLM-MiniLM-L12-v2",
        classification_enabled: true,
        classification_categories:
          "contract,invoice,receipt,report,book,personal_document,technical_document,correspondence,other",
        classification_confidence_threshold: 0.5,
        duplicate_detection_enabled: true,
        duplicate_similarity_threshold: 0.85,
      };
    }
  },

  // Auth
  login: async (email: string, password: string) => {
    return request<{ access_token: string; refresh_token: string; token_type: string }>(
      "/auth/login",
      { method: "POST", body: { email, password } },
    );
  },

  register: async (email: string, full_name: string, password: string) => {
    return request<{ access_token: string; refresh_token: string; token_type: string }>(
      "/auth/register",
      { method: "POST", body: { email, full_name, password } },
    );
  },

  // Health check
  checkBackendHealth: async (): Promise<boolean> => {
    try {
      await request<{ status: string }>("/health");
      return true;
    } catch {
      return false;
    }
  },

  // Document operations
  listDocuments: (req?: ListDocumentsRequest) =>
    request<DocumentListResponse>("/documents", {
      query: {
        folder_id: req?.folder_id,
        q: req?.q,
        skip: req?.skip ?? 0,
        limit: req?.limit ?? 50,
        include_deleted: req?.include_deleted ?? false,
      },
    }),

  getDocument: (documentId: string) =>
    request<DocumentMetadata>(`/documents/${documentId}`),

  uploadDocument: async (req: UploadDocumentRequest) => {
    const formData = new FormData();
    if (req.file) {
      formData.append("file", req.file);
    }
    if (req.title) {
      formData.append("title", req.title);
    }
    if (req.folder_id) {
      formData.append("folder_id", req.folder_id);
    }
    return requestFormData("/documents", formData) as Promise<{
      document_id: string;
      message: string;
      status: string;
    }>;
  },

  downloadDocument: async (documentId: string): Promise<string> => {
    const res = await fetch(`${API_BASE}/documents/${documentId}/download`);
    if (!res.ok) {
      throw new Error(`API ${res.status}: ${res.statusText}`);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    return url;
  },

  deleteDocument: async (documentId: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/documents/${documentId}`, {
      method: "DELETE",
    });
    if (!res.ok) {
      throw new Error(`API ${res.status}: ${res.statusText}`);
    }
  },

  // Folder operations
  listFolders: async (parent_id?: string): Promise<FolderInfo[]> => {
    return request<FolderInfo[]>("/folders", {
      query: parent_id ? { parent_id } : undefined,
    });
  },

  createFolder: async (req: FolderCreate): Promise<FolderInfo> => {
    return request<FolderInfo>("/folders", {
      method: "POST",
      body: req,
    });
  },

  // Tag operations
  listTags: async (): Promise<TagRead[]> => {
    return request<TagRead[]>("/tags");
  },

  createTag: async (req: TagCreate): Promise<TagRead> => {
    return request<TagRead>("/tags", {
      method: "POST",
      body: req,
    });
  },

  // Search operations
  searchDocuments: (req: SearchRequest) =>
    request<SearchResult[]>("/search/chunks", {
      query: {
        q: req.q,
        document_id: req.document_id ?? undefined,
        limit: req.limit ?? 30,
      },
    }),

  // AI / RAG
  askQuestion: async (req: AskRequest) => {
    return request<{ answer: string }>("/ask", {
      method: "POST",
      body: { query: req.query, document_id: req.document_id ?? undefined },
    });
  },
};

// ---------------------------------------------------------------------------
// Tauri desktop-only features (dialogs, notifications, shell)
// ---------------------------------------------------------------------------

export const dialog = {
  open: (options?: {
    multiple?: boolean;
    directories?: boolean;
    filters?: Array<{ name: string; extensions: string[] }>;
  }) =>
    openDialog({
      multiple: options?.multiple || false,
      directory: options?.directories || false,
      filters: options?.filters,
    }),

  save: (options?: { defaultPath?: string; filters?: any[] }) =>
    saveDialog({
      defaultPath: options?.defaultPath,
      filters: options?.filters,
    }),
};

export const notify = {
  success: (title: string, body?: string) =>
    sendNotification({
      title,
      body: body || "",
    }),

  error: (title: string, body?: string) =>
    sendNotification({
      title,
      body: body || "",
    }),

  info: (title: string, body?: string) =>
    sendNotification({
      title,
      body: body || "",
    }),
};

export const openExternal = (url: string) => open(url);

// Legacy-compatible method names (kept for existing call sites)
export const pickFolder = () => dialog.open({ directories: true });
export const scanFolder = (folderPath: string) => {
  console.log("scan_folder not implemented via HTTP:", folderPath);
  return Promise.resolve([]);
};
export const startFolderWatcher = (folderPath: string) => {
  console.log("start_folder_watcher not implemented via HTTP:", folderPath);
  return Promise.resolve("watcher not available");
};