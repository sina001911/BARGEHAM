# Report G — BARGEHAM Product Definition

**Product:** BARGEHAM — Intelligent file/document management platform  
**Constraint:** Native Windows desktop (EXE/MSI) + native Android companion (APK/AAB), NOT web-based  
**Status:** Research report — final product definition based on Reports A–F

---

## 1. Product Vision Statement

BARGEHAM helps users understand, organize, analyze, search, and manage the digital information stored on their devices using AI. It is a **local-first, privacy-respecting, native software product** with a Windows desktop application as the primary processing node and an Android mobile app as a companion. Persian language support is a core requirement.

**Tagline (from original concept):** *"اسناد را بگیر، بگرد، بپرس و بدان."* — "Take the document, search it, ask about it, and know it."

---

## 2. What BARGEHAM DOES

### A. Intelligent File Discovery
- Discovers files across user-authorized directories on Windows drives and Android storage
- Identifies file types, formats, sizes, dates, and metadata
- Recognizes documents, images, videos, audio, archives, source code, and project files
- Detects potentially important files (contracts, invoices, receipts, reports)
- Identifies duplicate and similar files (exact hash + near-duplicate detection)
- Identifies outdated and redundant documents

### B. Intelligent Document Understanding
- Reads PDF, DOCX, XLSX, PPTX, TXT, and scanned documents
- OCR for Persian, English, and multilingual documents (PaddleOCR primary, Tesseract fallback)
- Extracts tables, dates, names, amounts, organizations, and key information
- Automatically categorizes documents (contracts, invoices, receipts, reports, books, personal documents, technical documents, correspondence)
- Identifies relationships between documents

### C. Automatic Classification
- Classifies files by content and purpose (not just extension)
- Detects document types: contracts, invoices, receipts, reports, books, personal documents, technical documents, correspondence
- Recommends folder structures
- Suggests file naming improvements
- **Never moves or deletes files without explicit user approval**

### D. AI Knowledge Assistant
- Answers natural-language questions about local files
- Searches across multiple documents simultaneously
- Provides answers with source references (document name, page number)
- Identifies relevant documents and exact page numbers
- Summarizes documents
- Compares multiple documents
- Extracts structured information (dates, amounts, names)
- Generates reports based on available files

### E. Intelligent Recommendations
- Detects organizational problems (scattered files, inconsistent naming)
- Identifies missing or potentially related documents
- Recommends file organization improvements
- Detects duplicate document versions
- Identifies storage inefficiencies
- Provides actionable reports

### F. Privacy and Local Intelligence
- **Local-first processing:** OCR, embeddings, AI inference run locally by default
- **User-controlled cloud AI:** Optional cloud integration; user provides API key; nothing phones home by default
- **No mandatory cloud upload:** Files stay on the user's device
- **Explicit permission before scanning directories:** User selects which folders to index
- **Excludes sensitive and system directories by default:** No scanning of `C:\Windows`, `C:\Program Files`, Android app-private dirs, etc.
- **Transparent processing and storage:** User can see what was indexed and where data is stored
- **User-controlled data deletion and retention:** User can delete indexed data at any time

---

## 3. What BARGEHAM Does NOT Do

| Does Not Do | Reason |
|-------------|--------|
| Web-based dashboard as primary product | BARGEHAM is native software, not a website |
| Silent background scanning without permission | User must explicitly authorize directory access |
| Automatic file moves/deletes without approval | All file operations require explicit user consent |
| Mandatory cloud account | Local-first; cloud is optional |
| Selling user data | Privacy-first; no telemetry by default |
| Replacing Windows File Explorer or Android Files app | Companion tool, not a shell replacement |
| Scanning entire Android device without user selection | Android scoped storage prohibits this; user picks folders via SAF |
| Real-time continuous background indexing on Android | Android background restrictions make this unreliable |
| Cloud-only AI models | Local inference is default; cloud AI is optional |

---

## 4. Core User Flows

### Flow 1: First Setup (Windows)
1. User installs BARGEHAM (MSI/EXE)
2. App requests permission to index specific directories (user picks via folder browser)
3. App scans selected directories, extracts metadata, stores in local PostgreSQL
4. For scanned documents: OCR runs (PaddleOCR Persian/English)
5. Embeddings generated for text content (Persian model)
6. User sees indexing complete notification; can start searching

### Flow 2: Asking a Question (Windows)
1. User opens BARGEHAM, navigates to AI Assistant
2. Types question in Persian or English: "چه فاکتورهایی در月底 پرداخت شده‌اند؟" (What invoices were paid at month end?)
3. System performs hybrid search (FTS + vector + RRF) across indexed documents
4. Top chunks sent to local LLM (Ollama) with system prompt
5. Answer returned with citations: [page 3], [invoice_2024.pdf, page 1]
6. User can click citation to open document at page

### Flow 3: Adding Files from Android
1. User opens BARGEHAM Android app
2. Selects "Add files" → system photo picker or SAF folder picker
3. User selects PDF/image files; persistable URI permission granted
4. Files processed locally on Android (OCR, embedding, indexing)
5. Sync queued; uploaded to BARGEHAM cloud relay when network available
6. Windows app downloads synced documents and index updates

### Flow 4: File Organization Recommendation
1. User requests "Organize my Documents folder"
2. BARGEHAM analyzes all files in the folder
3. Detects: invoices scattered across subfolders, duplicate versions, inconsistent naming
4. Recommends: move invoices to `/Documents/Invoices/2024/`, rename `scan1.pdf` to `invoice_acme_2024_03.pdf`, delete duplicate `copy_of_report_final_v2.pdf`
5. **User reviews each recommendation; nothing changes without explicit approval**

---

## 5. Platform Roles

| Aspect | Windows Desktop | Android Mobile |
|--------|----------------|----------------|
| Primary role | Main indexing and processing node | Companion for access and search |
| File discovery | Full directory scanning (user-authorized) | User-picked folders + MediaStore |
| OCR | PaddleOCR + Tesseract (full power) | ML Kit bundled (on-device, offline) |
| Embeddings | sentence-transformers (Persian model) | ONNX Runtime Mobile (lighter models) |
| Vector search | pgvector (PostgreSQL) | sqlite-vec (via NDK) |
| Full-text search | PostgreSQL FTS | SQLite FTS5 |
| LLM inference | Ollama (local models) | Limited; cloud fallback optional |
| Background indexing | Windows service / background task | Foreground service (user-initiated batches) |
| Sync | Cloud relay client | Cloud relay client |
| Notifications | System tray + Windows notifications | Push notifications + foreground service |

---

## 6. Success Metrics (MVP)

| Metric | Target |
|--------|--------|
| Documents indexed per hour (Windows) | 1,000+ (text-based), 100+ (scanned with OCR) |
| OCR accuracy (Persian, clean scans) | >85% |
| Semantic search relevance (top-5) | >80% user satisfaction |
| App install size (Windows) | <150 MB |
| App install size (Android) | <50 MB |
| Time to first search after install | <5 minutes |
| Local processing (default) | 100% of OCR, embeddings, search |
| Persian UI completeness | 100% of core screens |

---

## 7. Non-Goals (Explicitly Out of Scope for MVP)

- Cloud-only document storage (files remain local by default)
- Multi-user collaboration / shared document libraries
- Real-time collaborative editing
- Integration with third-party cloud storage (Google Drive, Dropbox, OneDrive) as primary storage — optional sync only
- Mobile-native document creation (editing Word/Excel on Android)
- Barcode/QR code scanning
- Voice-to-text document dictation
- Integration with Windows Explorer context menu (beyond file associations)
- Automatic backup to cloud (user must opt in)

---

## 8. Differentiation Summary

| Differentiator | How BARGEHAM Delivers |
|---------------|----------------------|
| Native Windows + Native Android | Tauri 2 (Windows) + Kotlin Compose (Android) |
| Local-first AI | Ollama + sentence-transformers run locally |
| Persian as core language | PaddleOCR `fa` model + Msobhi embedding + RTL UI |
| Explicit user approval | No silent file moves/deletes |
| Android scoped storage compliant | SAF + MediaStore; no `MANAGE_EXTERNAL_STORAGE` |
| Intelligent recommendations | Proactive org insights, not just search |
| Hybrid search (FTS + vector + RRF) | Better relevance than keyword-only |
| Open-source-friendly components | MIT/Apache-2.0 libraries; no AGPL |

---

## Sources

- Report A — Competitor Landscape: /d/BARGEHAM/RESEARCH_REPORT_A_Competitor_Landscape.md
- Report B — Feature Comparison Matrix: /d/BARGEHAM/RESEARCH_REPORT_B_Feature_Comparison_Matrix.md
- Report C — Open-Source Reuse: /d/BARGEHAM/RESEARCH_REPORT_C_OpenSource_Reuse.md
- Report D — Windows Architecture: /d/BARGEHAM/RESEARCH_REPORT_D_Windows_Architecture.md
- Report E — Android Architecture: /d/BARGEHAM/RESEARCH_REPORT_E_Android_Architecture.md
- Report F — Persian AI and OCR: /d/BARGEHAM/RESEARCH_REPORT_F_Persian_AI_OCR.md
