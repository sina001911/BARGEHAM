import { create } from "zustand";
import { api } from "@/lib/api";
import type {
  DocumentMetadata,
  DocumentListResponse,
  FolderInfo,
  SearchResult,
} from "@/types";

interface AppState {
  // Auth
  token: string | null;
  setToken: (token: string | null) => void;

  // Backend status
  backendOnline: boolean;
  setBackendOnline: (online: boolean) => void;

  // Documents
  documents: DocumentMetadata[];
  total: number;
  loading: boolean;
  error: string | null;
  setDocuments: (docs: DocumentMetadata[], total: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  addDocument: (doc: DocumentMetadata) => void;
  updateDocument: (id: string, updates: Partial<DocumentMetadata>) => void;
  removeDocument: (id: string) => void;
  fetchDocuments: (
    folderId?: string,
    q?: string,
    skip?: number,
    limit?: number,
  ) => Promise<void>;
  fetchDocument: (documentId: string) => Promise<void>;
  currentDoc: DocumentMetadata | null;

  // Current folder
  currentFolder: FolderInfo | null;
  setCurrentFolder: (folder: FolderInfo | null) => void;

  // Search
  searchResults: Array<{
    chunk_id: string;
    document_id: string;
    page_number: number;
    section: string | null;
    direction: string;
    text: string;
    score: number;
  }>;
  setSearchResults: (results: any[]) => void;

  // Answer
  answer: string;
  setAnswer: (answer: string) => void;
}

export const useStore = create<AppState>((set, get) => ({
  // Auth
  token: null,
  setToken: (token) => set({ token }),

  // Backend status
  backendOnline: false,
  setBackendOnline: (online) => set({ backendOnline: online }),

  // Documents
  documents: [],
  total: 0,
  loading: false,
  error: null,
  currentDoc: null,
  setDocuments: (docs, total) => set({ documents: docs, total }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  addDocument: (doc) =>
    set((state) => ({ documents: [doc, ...state.documents] })),
  updateDocument: (id, updates) =>
    set((state) => ({
      documents: state.documents.map((d) =>
        d.id === id ? { ...d, ...updates } : d
      ),
    })),
  removeDocument: (id) =>
    set((state) => ({ documents: state.documents.filter((d) => d.id !== id) })),
  fetchDocuments: async (folderId, q, skip = 0, limit = 50) => {
    set({ loading: true, error: null });
    try {
      const result = await api.listDocuments({
        folder_id: folderId,
        q,
        skip,
        limit,
        include_deleted: false,
      });
      set({ documents: result.items, total: result.total, loading: false });
    } catch (err: any) {
      set({ error: err.message || "Failed to load documents", loading: false });
    }
  },
  fetchDocument: async (documentId) => {
    set({ loading: true, error: null });
    try {
      const doc = await api.getDocument(documentId);
      set({ currentDoc: doc, loading: false });
    } catch (err: any) {
      set({ error: err.message || "Failed to load document", loading: false });
    }
  },

  // Current folder
  currentFolder: null,
  setCurrentFolder: (folder) => set({ currentFolder: folder }),

  // Search
  searchResults: [],
  setSearchResults: (results) => set({ searchResults: results }),

  // Answer
  answer: "",
  setAnswer: (answer: string) => set({ answer }),
}));
