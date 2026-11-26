# Report H — Product Roadmap

**Product:** BARGEHAM — Intelligent file/document management platform  
**Constraint:** Native Windows desktop (EXE/MSI) + native Android companion (APK/AAB)  
**Persian language:** Core requirement from Phase 1  
**Status:** Research report — phased roadmap based on Reports A–G

---

## Roadmap Overview

| Phase | Focus | Duration | Platform | Key Deliverable |
|-------|-------|----------|----------|-----------------|
| Phase 0 | Research and audit | Complete | Both | This report series (Reports A–I) |
| Phase 1 | Core file discovery and indexing | Months 1–3 | Windows | Windows app scans user folders, extracts metadata, local search |
| Phase 2 | Document intelligence and classification | Months 4–6 | Windows | OCR (Persian/English), auto-classification, duplicate detection |
| Phase 3 | Search and AI assistant | Months 7–9 | Windows | Hybrid search (FTS+vector+RRF), RAG chat with citations |
| Phase 4 | Analysis and recommendations | Months 10–12 | Windows | Intelligent recommendations, org insights, storage analysis |
| Phase 5 | Android application | Months 13–18 | Android | Native Android app, SAF file access, on-device OCR, local search |
| Phase 6 | Cross-device synchronization | Months 19–21 | Both | Cloud relay sync, offline-first queue, Windows<->Android |
| Phase 7 | Advanced intelligence and automation | Months 22–24 | Both | Advanced AI features, automation rules, smart folders |

**Total timeline:** ~24 months to full vision  
**MVP target:** End of Phase 3 (Month 9) — Windows-only MVP with search + RAG

---

## Phase 0: Research and Audit (Complete)

**Duration:** Complete  
**Platform:** Both  

**Deliverables:**
- Report A — Competitor Landscape
- Report B — Feature Comparison Matrix
- Report C — Open-Source Reuse Opportunities
- Report D — Windows Architecture
- Report E — Android Architecture
- Report F — Persian AI and OCR Assessment
- Report G — BARGEHAM Product Definition
- Report H — Product Roadmap (this document)
- Report I — Final Strategic Recommendation

**Exit criteria:** All reports completed; technology stack selected; go/no-go decision made.

---

## Phase 1: Core File Discovery and Indexing (Months 1–3)

**Platform:** Windows Desktop  
**Goal:** Build the foundation — a Windows app that can discover, scan, and index user-authorized files.

### Objectives
1. Native Windows desktop application (Tauri 2 or .NET) with installer (MSI/EXE)
2. User selects directories to index (explicit permission, no silent scanning)
3. Recursive file discovery with metadata extraction (size, dates, MIME type)
4. Local PostgreSQL + pgvector database for metadata storage
5. Basic keyword search over file names and metadata
6. File system monitoring for new/modified files in indexed directories
7. Persian UI (RTL layout, `lang="fa"`)

### Key Features
| Feature | Description |
|---------|-------------|
| Directory picker | Windows folder browser dialog; user selects which folders to index |
| Metadata extraction | File size, creation/modification dates, MIME type (via `filetype` library) |
| File type filtering | User-configurable allowed extensions (default: .pdf, .docx, .xlsx, .pptx, .txt, images) |
| SQLite FTS5 fallback | Full-text search on file names if PostgreSQL not yet configured |
| File system watcher | `watchdog` or Rust `notify` crate for real-time change detection |
| Persian UI | RTL layout, Persian font (Vazir), right-to-left direction |

### Technical Tasks
- [ ] Set up Tauri 2 project with Rust backend
- [ ] Integrate Python backend (FastAPI) via sidecar or embedded
- [ ] Set up local PostgreSQL 16 + pgvector
- [ ] Implement directory picker and permission flow
- [ ] Implement recursive file scanner (walkdir / os.walk)
- [ ] Implement metadata extraction and DB storage
- [ ] Implement file system watcher for indexed directories
- [ ] Implement basic keyword search
- [ ] Implement Persian RTL UI
- [ ] Build MSI/EXE installer
- [ ] Code-sign with EV certificate

### Exit Criteria
- Windows app installs and runs on Windows 10/11
- User can select directories and see them indexed
- Keyword search returns results from indexed file names/metadata
- New files in indexed directories are detected automatically
- Persian UI displays correctly (RTL)

---

## Phase 2: Document Intelligence and Classification (Months 4–6)

**Platform:** Windows Desktop  
**Goal:** Add document understanding — OCR, text extraction, classification, duplicate detection.

### Objectives
1. OCR for scanned documents (PaddleOCR Persian + English, Tesseract fallback)
2. Text extraction from PDF, DOCX, XLSX, PPTX, TXT
3. Document auto-classification (contracts, invoices, receipts, reports, etc.)
4. Duplicate detection (exact SHA-256 + near-duplicate MinHash)
5. Chunking and embedding generation for semantic search
6. Persian OCR validation with real documents

### Key Features
| Feature | Description |
|---------|-------------|
| OCR pipeline | PaddleOCR primary (Persian `fa` model), Tesseract fallback |
| Text extraction | pdfplumber (PDF), python-docx (DOCX), openpyxl (XLSX) |
| Document classification | Zero-shot classification via sentence-transformers |
| Duplicate detection | SHA-256 for exact; MinHash+LSH for near-duplicates |
| Document chunking | Paragraph-aware splitting with overlap (900 char chunks, 150 overlap) |
| Embedding generation | Msobhi/Persian_Sentence_Embedding_v3 |
| Embedding storage | pgvector column on text chunks |

### Technical Tasks
- [ ] Integrate PaddleOCR with Persian language model
- [ ] Integrate Tesseract + fas as fallback
- [ ] Integrate pdfplumber, python-docx, openpyxl
- [ ] Implement document processing pipeline (file → text → chunks → embeddings)
- [ ] Implement zero-shot document classification
- [ ] Implement duplicate detection
- [ ] Store embeddings in pgvector
- [ ] Add OCR confidence scoring
- [ ] Add language detection (Persian vs English vs mixed)
- [ ] Test OCR on real Persian scanned documents

### Exit Criteria
- Scanned Persian and English documents are OCR'd with acceptable accuracy
- Text-extractable documents are processed without OCR
- Documents are auto-classified with reasonable accuracy
- Duplicate documents are detected
- Embeddings stored and queryable

---

## Phase 3: Search and AI Assistant (Months 7–9)

**Platform:** Windows Desktop  
**Goal:** Enable users to find and ask about their documents — the core value proposition.

### Objectives
1. Hybrid search: full-text (PostgreSQL FTS) + vector (pgvector cosine similarity) + RRF fusion
2. RAG AI assistant: chat with documents, cited answers with page references
3. Ollama integration for local LLM inference
4. Document viewer with page-level navigation
5. Search filters (file type, date range, tags, language)
6. Persian-English mixed query support

### Key Features
| Feature | Description |
|---------|-------------|
| Hybrid search | FTS + vector + Reciprocal Rank Fusion |
| RAG chat | Ask questions about documents; answers cite sources |
| Page-level citations | [page N] references in answers |
| Document viewer | View extracted text page by page |
| Search filters | File type, date, language, tags, folder |
| Mixed Persian-English queries | bge-m3 multilingual embedding |
| Search history | Recent queries and results |

### Technical Tasks
- [ ] Implement PostgreSQL FTS with Persian configuration
- [ ] Implement pgvector cosine similarity search
- [ ] Implement RRF fusion for hybrid results
- [ ] Integrate Ollama for local LLM inference
- [ ] Implement RAG pipeline (retrieve → augment → generate)
- [ ] Implement page-level citation extraction
- [ ] Build document viewer UI
- [ ] Build search UI with filters
- [ ] Implement search history
- [ ] Test RAG accuracy with Persian queries

### Exit Criteria
- User can search across all indexed documents
- RAG answers cite source documents and page numbers
- Persian and English queries work
- Hybrid search returns relevant results
- Document viewer displays extracted text

**MVP READY:** End of Phase 3 — Windows-only product with core search + RAG value proposition.

---

## Phase 4: Analysis and Recommendations (Months 10–12)

**Platform:** Windows Desktop  
**Goal:** Move from search to proactive intelligence — recommendations and insights.

### Objectives
1. Detect organizational problems (scattered files, inconsistent naming)
2. Identify missing or potentially related documents
3. Recommend folder structures and naming improvements
4. Detect duplicate document versions
5. Identify storage inefficiencies
6. Generate actionable reports

### Key Features
| Feature | Description |
|---------|-------------|
| Org problem detection | Scattered files, naming inconsistencies, deep nesting |
| Related document detection | Documents that should be together but aren't |
| Folder structure recommendations | Suggested reorganization based on content analysis |
| Naming improvement suggestions | Consistent naming conventions |
| Duplicate version detection | Multiple versions of the same document |
| Storage analysis | Large files, old files, unused files |
| Actionable reports | Exportable PDF/HTML reports with recommendations |
| Approval workflow | User reviews and approves each recommendation before action |

### Technical Tasks
- [ ] Implement file organization analysis algorithms
- [ ] Implement related document detection (semantic similarity)
- [ ] Implement folder structure recommendation engine
- [ ] Implement naming convention suggestion
- [ ] Implement storage analysis (size, age, usage)
- [ ] Build recommendations UI with approval workflow
- [ ] Implement report generation (PDF/HTML)
- [ ] Implement safe file operations (move/rename/delete with user confirmation)
- [ ] Test recommendation accuracy

### Exit Criteria
- User receives actionable organization recommendations
- Recommendations require explicit user approval before execution
- Reports can be generated and exported
- File operations are safe (no silent changes)

---

## Phase 5: Android Application (Months 13–18)

**Platform:** Android Mobile  
**Goal:** Native Android companion app for document access and search on mobile.

### Objectives
1. Native Android app (Kotlin + Jetpack Compose) distributed as APK/AAB
2. User-picked folder access via Storage Access Framework (SAF)
3. MediaStore access for images/videos
4. On-device OCR (ML Kit bundled, offline)
5. Local search (SQLite FTS5 + sqlite-vec)
6. Document viewer for extracted text
7. Persisted URI permissions for folder access across reboots

### Key Features
| Feature | Description |
|---------|-------------|
| SAF folder picker | User selects folders to index (ACTION_OPEN_DOCUMENT_TREE) |
| Photo picker | User selects individual files (PickVisualMedia) |
| Persisted URI grants | Remember folder access across reboots |
| On-device OCR | ML Kit bundled (offline, API 23+) |
| Local search | SQLite FTS5 + sqlite-vec vector search |
| Document viewer | View extracted text, page-by-page PDF rendering |
| Sync queue | Offline-first; sync when network available |
| Persian UI | RTL layout in Compose |

### Technical Tasks
- [ ] Set up Android project (Kotlin + Jetpack Compose + Gradle)
- [ ] Implement SAF folder and file picking
- [ ] Implement persisted URI permissions
- [ ] Integrate ML Kit bundled OCR
- [ ] Integrate PdfRenderer for PDF page rendering
- [ ] Implement Room/SQLite local database
- [ ] Integrate sqlite-vec for vector search (via NDK)
- [ ] Implement local search UI
- [ ] Implement document viewer
- [ ] Implement Persian RTL UI in Compose
- [ ] Build APK/AAB for distribution
- [ ] Test on multiple Android versions (API 29–35)

### Exit Criteria
- Android app installs and runs on API 29+
- User can pick folders and see files indexed
- On-device OCR works offline
- Local search returns results
- Persian RTL UI displays correctly

---

## Phase 6: Cross-Device Synchronization (Months 19–21)

**Platform:** Both Windows and Android  
**Goal:** Sync documents and index between Windows and Android via cloud relay.

### Objectives
1. Cloud relay server (BARGEHAM-operated or user self-hosted)
2. Offline-first sync queue (create/update/delete with timestamps)
3. Delta sync (only changed documents)
4. Conflict resolution (last-write-wins or user-visible conflict UI)
5. Sync on app launch or when network available (WorkManager UNMETERED)
6. No requirement for simultaneous online presence

### Key Features
| Feature | Description |
|---------|-------------|
| Cloud relay | Central sync service (optional; user can self-host) |
| Offline-first queue | Changes queued locally; synced when online |
| Delta sync | Only document changes transferred |
| Conflict resolution | Last-write-wins + user-visible conflicts |
| Opportunistic sync | WorkManager on Android; background task on Windows |
| Sync status UI | Show sync progress and status |
| Selective sync | User chooses which folders to sync |

### Technical Tasks
- [ ] Design sync protocol (gRPC or REST)
- [ ] Build cloud relay server
- [ ] Implement offline-first sync queue (Room on Android, local table on Windows)
- [ ] Implement delta sync logic
- [ ] Implement conflict detection and resolution
- [ ] Implement sync scheduling (WorkManager Android, background task Windows)
- [ ] Build sync status UI
- [ ] Implement selective sync (folder-level)
- [ ] Test sync reliability (interrupted connections, conflicts)

### Exit Criteria
- Documents indexed on Windows appear on Android and vice versa
- Sync works with intermittent connectivity
- Conflicts are resolved or presented to user
- Sync does not require both devices online simultaneously

---

## Phase 7: Advanced Intelligence and Automation (Months 22–24)

**Platform:** Both  
**Goal:** Advanced AI features and automation — the long-term vision.

### Objectives
1. Automation rules (if document type = invoice, tag = finance, folder = /Invoices)
2. Smart folders (auto-populated by content rules)
3. Advanced AI: document summarization, comparison, structured extraction
4. Cross-document analysis (compare contracts, find inconsistencies)
5. Scheduled reports (weekly organization digest)
6. Third-party integrations (optional)

### Key Features
| Feature | Description |
|---------|-------------|
| Automation rules | User-defined rules for tagging/folder assignment |
| Smart folders | Virtual folders based on content rules |
| Document summarization | AI-generated summaries of long documents |
| Document comparison | Side-by-side comparison of two documents |
| Structured extraction | Extract invoices data (amount, date, vendor) to CSV/Excel |
| Scheduled reports | Weekly/monthly organization and storage reports |
| API for integrations | Optional REST API for third-party tools |

### Technical Tasks
- [ ] Implement automation rule engine
- [ ] Implement smart folders (virtual collections)
- [ ] Implement document summarization (local LLM)
- [ ] Implement document comparison UI
- [ ] Implement structured data extraction
- [ ] Implement scheduled report generation
- [ ] Build optional REST API
- [ ] Test advanced AI accuracy

### Exit Criteria
- Automation rules work reliably
- Smart folders auto-populate correctly
- Structured extraction produces usable data
- Scheduled reports generated on time

---

## MVP Scope Definition

**MVP = End of Phase 3 (Month 9), Windows only**

| Included in MVP | Postponed to Later |
|-----------------|-------------------|
| Native Windows desktop app | Android app (Phase 5) |
| Directory scanning and indexing | Cloud sync (Phase 6) |
| OCR (Persian + English) | Advanced AI (Phase 7) |
| Document classification | Automation rules (Phase 7) |
| Duplicate detection | Smart folders (Phase 7) |
| Hybrid search (FTS + vector + RRF) | Third-party integrations (Phase 7) |
| RAG AI assistant with citations | Scheduled reports (Phase 7) |
| Persian RTL UI | |
| Local-first processing | |
| Explicit user approval for file operations | |

---

## Risks and Mitigations by Phase

| Phase | Top Risk | Mitigation |
|-------|----------|------------|
| Phase 1 | Windows Defender false positive | Code signing; submit to Microsoft |
| Phase 2 | Persian OCR accuracy below expectations | Test early with real documents; allow user correction |
| Phase 3 | RAG hallucination | Conservative system prompt; cite sources; allow user feedback |
| Phase 4 | Recommendations feel intrusive | Opt-in; explicit approval for every action |
| Phase 5 | Android scoped storage limits | Design around SAF + MediaStore; clear user messaging |
| Phase 6 | Sync reliability on battery-restricted Android | Cloud relay; sync on app launch; offline-first |
| Phase 7 | Advanced AI complexity | Start simple; add features incrementally |

---

## Success Criteria by Phase

| Phase | Success Criteria |
|-------|-----------------|
| Phase 1 | Windows app installed; directories indexed; keyword search works |
| Phase 2 | OCR on Persian/English documents; classification; duplicates detected |
| Phase 3 | Hybrid search; RAG answers with citations; Persian queries work |
| Phase 4 | Recommendations generated; user approves actions; reports exported |
| Phase 5 | Android app installed; SAF folders indexed; offline OCR works |
| Phase 6 | Documents sync Windows↔Android; conflicts resolved |
| Phase 7 | Automation rules; smart folders; structured extraction |

---

## Sources

- Report A–G: All previous research reports in /d/BARGEHAM/
- Android scoped storage: https://developer.android.com/training/data-storage
- Tauri 2: https://tauri.app/
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- Ollama: https://github.com/ollama/ollama
- pgvector: https://github.com/pgvector/pgvector
