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

// --------------------------------------------------------------------------- //
// Academy — Courses
// --------------------------------------------------------------------------- //
export interface Course {
  id: string;
  name: string;
  description: string | null;
  course_type: string;
  owner_id: string;
  is_active: boolean;
  documents_indexed: number;
  chunks_indexed: number;
  lessons_completed: number;
  quizzes_taken: number;
  average_score: number;
  created_at: string;
  updated_at: string;
}

export interface CourseCreate {
  name: string;
  description?: string;
  course_type?: string;
}

// --------------------------------------------------------------------------- //
// Academy — Lessons
// --------------------------------------------------------------------------- //
export interface Lesson {
  id: string;
  course_id: string;
  topic: string;
  title: string;
  content: string;
  lesson_type: string;
  status: string;
  order_index: number;
  estimated_minutes: number | null;
  ai_generated: boolean;
  created_at: string;
  updated_at: string;
}

// --------------------------------------------------------------------------- //
// Academy — Quizzes
// --------------------------------------------------------------------------- //
export interface QuizQuestion {
  id: string;
  quiz_id: string;
  question_text: string;
  options: string[];
  correct_answer: string;
  explanation: string | null;
}

export interface Quiz {
  id: string;
  course_id: string;
  title: string;
  quiz_type: string;
  status: string;
  questions: QuizQuestion[];
  created_at: string;
}

export interface QuizAttempt {
  id: string;
  quiz_id: string;
  user_id: string;
  score: number;
  total_questions: number;
  answers: Record<string, string>;
  status: string;
  started_at: string;
  completed_at: string | null;
}

// --------------------------------------------------------------------------- //
// Academy — Flashcards
// --------------------------------------------------------------------------- //
export interface Flashcard {
  id: string;
  course_id: string;
  user_id: string;
  front: string;
  back: string;
  ease_factor: number;
  interval_days: number;
  repetitions: number;
  due_date: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

// --------------------------------------------------------------------------- //
// Academy — Socratic Session
// --------------------------------------------------------------------------- //
export interface SocraticMessage {
  role: "user" | "assistant";
  content: string;
  mode: string;
  timestamp: string;
}

export interface SocraticSession {
  id: string;
  course_id: string;
  user_id: string;
  topic: string;
  messages: SocraticMessage[];
  status: string;
  created_at: string;
  updated_at: string;
}

// --------------------------------------------------------------------------- //
// Academy — Learner Memory & Progress
// --------------------------------------------------------------------------- //
export interface LearnerMemory {
  id: string;
  course_id: string;
  user_id: string;
  topic: string;
  mastery_level: number;
  confidence: number;
  mistakes: string | null;
  weaknesses: string | null;
  goals: string | null;
  progress_summary: string | null;
  updated_at: string;
  created_at: string;
}

export interface LearningAnalytics {
  courses_enrolled: number;
  lessons_completed: number;
  quizzes_taken: number;
  flashcards_reviewed: number;
  average_quiz_score: number;
  streak_days: number;
  topics_mastered: number;
}

// --------------------------------------------------------------------------- //
// Audio Library
// --------------------------------------------------------------------------- //
export interface AudioFile {
  id: string;
  title: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  duration_seconds: number | null;
  bitrate: number | null;
  sample_rate: number | null;
  channels: number | null;
  codec: string | null;
  status: string;
  language: string | null;
  has_transcript: boolean;
  transcript_confidence: number | null;
  summary: string | null;
  created_at: string;
}

export interface AudioChapter {
  id: string;
  audio_id: string;
  title: string;
  start_seconds: number;
  end_seconds: number | null;
  order_index: number;
}

export interface TranscriptSegment {
  id: string;
  audio_id: string;
  segment_index: number;
  start_seconds: number;
  end_seconds: number;
  text: string;
  speaker: string | null;
  confidence: number | null;
}

export interface AudioPlaylist {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}
