export interface DocumentMetadata {
  id: string;
  path: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  document_type: string;
  status: string;
  version: number;
  page_count: number | null;
  language: string | null;
  has_text_layer: boolean;
  ocr_confidence: number | null;
  created_at: string;
  updated_at: string;
  folder_id: string | null;
  owner_id: string | null;
  // Classification
  classification: string | null;
  classification_confidence: number | null;
  classification_version: number;
  // Duplicate detection
  content_hash: string | null;
  duplicate_of: string | null;
  duplicate_similarity: number | null;
  // Chunks
  chunks: any[];
}

export interface FolderInfo {
  id: string;
  name: string;
  path: string;
  parent_id: string | null;
  owner_id: string | null;
  created_at: string;
}

export interface UploadDocumentRequest {
  file: File;
  title?: string;
  folder_id?: string;
}

export interface UploadDocumentResponse {
  document_id: string;
  message: string;
  status: string;
}

export interface FolderCreate {
  name: string;
  parent_id?: string;
  owner_id?: string;
}

export interface TagRead {
  id: string;
  name: string;
  color: string | null;
  created_at: string;
}

export interface TagCreate {
  name: string;
  color?: string;
}

export interface ListDocumentsRequest {
  folder_id?: string;
  q?: string;
  skip?: number;
  limit?: number;
  include_deleted?: boolean;
}

export interface DocumentListResponse {
  items: DocumentMetadata[];
  total: number;
  skip: number;
  limit: number;
}

export interface SearchRequest {
  q: string;
  document_id?: string;
  limit?: number;
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  page_number: number;
  section: string | null;
  direction: string;
  text: string;
  score: number;
}

export interface AskRequest {
  query: string;
  document_id?: string;
  limit?: number;
}

export interface AskResponse {
  answer: string;
}

export interface AppConfig {
  api_base_url: string;
  max_upload_size_mb: number;
  allowed_mime_types: string[];
  ocr_engine: string;
  embedding_model: string;
  classification_enabled: boolean;
  classification_categories: string;
  classification_confidence_threshold: number;
  duplicate_detection_enabled: boolean;
  duplicate_similarity_threshold: number;
}

export interface AuthState {
  token: string | null;
  user: {
    id: string;
    email: string;
    full_name: string;
    is_active: boolean;
    is_superuser: boolean;
  } | null;
}

export interface DuplicateResult {
  is_exact_duplicate: boolean;
  exact_match_id: string | null;
  is_near_duplicate: boolean;
  near_match_id: string | null;
  near_similarity: number;
  content_hash: string;
}
