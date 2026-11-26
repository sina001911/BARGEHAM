# Report D — Windows Architecture

**Product:** BARGEHAM — Intelligent file/document management platform  
**Constraint:** Native Windows desktop application (installable EXE/MSI), NOT web-based  
**Status:** Research report — verified against technology documentation and repositories

---

## Executive Summary

BARGEHAM for Windows should be a **native desktop application** built with **Tauri 2** (Rust backend + webview frontend) or **.NET (WPF/WinUI 3)**. The backend runs a local API server (FastAPI/Python or ASP.NET Core) for document processing, OCR, indexing, and AI inference. Local PostgreSQL with pgvector stores metadata and embeddings. File system monitoring uses Windows ReadDirectoryChangesW (via watchdog or native Rust/Win32 API).

---

## Recommended Technology Stack

### Option A: Tauri 2 (Recommended)

| Layer | Technology | License | Notes |
|-------|-----------|---------|-------|
| Desktop Framework | **Tauri 2** | MIT/Apache-2.0 | Cross-platform desktop; Rust backend; system webview frontend |
| Backend Language | **Rust** | MIT/Apache-2.0 | Memory-safe, high performance, excellent Windows API bindings |
| Frontend | **React / Vue / Svelte** | MIT | Runs in system webview (Edge WebView2 on Windows) |
| Local API | **FastAPI (Python)** | MIT | Document processing, OCR, RAG, AI endpoints |
| Database | **PostgreSQL 16 + pgvector** | PostgreSQL/MIT | Local metadata + vector embeddings |
| File Monitoring | **Windows ReadDirectoryChangesW** (via Rust std or notify crate) | MIT/Apache-2.0 | Native Windows file system events |
| OCR | **PaddleOCR + Tesseract** | Apache-2.0 | Persian support via PaddleOCR fa model |
| LLM Inference | **Ollama** (local) | MIT | Local model serving via API |
| Embeddings | **sentence-transformers** | MIT | Persian model: Msobhi/Persian_Sentence_Embedding_v3 |
| Packaging | **Tauri bundler** + **MSIX/WIX** | MIT | EXE/MSI installer generation |

**Why Tauri 2:**
- Smaller binary than Electron (no bundled Chromium; uses system WebView2)
- Rust backend gives direct access to Windows APIs (file system, registry, notifications)
- MIT/Apache-2.0 license (permissive)
- Can bundle Python backend via PyO3 or sidecar process
- Auto-updater built-in

**Why NOT Electron:**
- Bundles Chromium (~100+ MB); larger install size
- More memory overhead
- Web-based architecture conflicts with "native software" requirement

**Why NOT .NET (WPF/WinUI 3):**
- Strong Windows integration but steep learning curve for non-.NET team
- Python backend integration requires interop (pythonnet or subprocess)
- Linux/macOS portability limited if future expansion needed

**Why NOT Qt:**
- Commercial license required for proprietary use (LGPL has obligations)
- Python bindings (PyQt/PySide) add complexity
- Heavier than Tauri for simple desktop apps

---

## Windows Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    BARGEHAM Windows App                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Tauri 2 Frontend (WebView2 / React/Vue/Svelte)        │  │
│  │  • RTL Persian UI                                       │  │
│  │  • File browser, document viewer, search                │  │
│  │  • AI chat interface (RAG)                              │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Tauri 2 Backend (Rust)                                │  │
│  │  • Window management, native menus, notifications       │  │
│  │  • File system monitoring (ReadDirectoryChangesW)       │  │
│  │  • IPC bridge to Python backend                         │  │
│  │  • Auto-updater, installer (MSI/EXE)                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Python Backend (FastAPI sidecar / embedded)           │  │
│  │  • Document processing pipeline                         │  │
│  │  • OCR (PaddleOCR + Tesseract fallback)                 │  │
│  │  • Embedding generation (sentence-transformers)         │  │
│  │  • RAG retrieval + LLM inference (Ollama)               │  │
│  │  • Classification, duplicate detection                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Local Data Layer                                       │  │
│  │  • PostgreSQL 16 + pgvector (metadata + embeddings)     │  │
│  │  • SQLite FTS5 (full-text search fallback)              │  │
│  │  • Local file storage (user-selected directories)       │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  External Services (optional, user-controlled)          │  │
│  │  • Ollama (local LLM inference)                         │  │
│  │  • Cloud sync (BARGEHAM relay, user opts in)            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Windows-Specific Features

### 1. File System Integration

| Feature | Windows API | Implementation |
|---------|------------|----------------|
| Directory scanning | `FindFirstFileW` / `FindNextFileW` | Rust `walkdir` crate or Python `os.walk` |
| File system monitoring | `ReadDirectoryChangesW` | Rust `notify` crate or Python `watchdog` |
| NTFS metadata | `GetFileInformationByHandleEx` | Rust `windows-rs` crate |
| File icons/thumbnails | `SHGetFileInfo` | Rust `windows-rs` or Win32 API |
| Shell integration | Shell extensions / context menu | Rust + registry registration |
| File associations | Registry `HKEY_CLASSES_ROOT` | MSI installer registers `.pdf`, `.docx`, etc. |

### 2. Background Operation

| Feature | Windows Mechanism | Implementation |
|---------|------------------|----------------|
| Background indexing | Windows Service or background task | Rust service or Python subprocess |
| Startup launch | Registry Run key or Task Scheduler | MSI installer configures |
| System tray notification | `Shell_NotifyIcon` | Tauri system tray API |
| Power management | `SetThreadExecutionState` | Prevent sleep during indexing |
| File locks | `CreateFile` with `FILE_SHARE_READ` | Handle concurrent access |

### 3. Installer and Distribution

| Component | Technology | Notes |
|-----------|-----------|-------|
| Installer format | **MSI** (WiX Toolset) or **EXE** (Inno Setup / NSIS) | MSI preferred for enterprise deployment |
| Code signing | EV Code Signing Certificate | Required for Windows SmartTrust |
| Auto-update | Tauri auto-updater | GitHub releases or private update server |
| Installation directory | `C:\Program Files\BARGEHAM` or `C:\Users\<user>\AppData\Local\BARGEHAM` | User-selectable |
| Data directory | `%LOCALAPPDATA%\BARGEHAM\` | Database, indexes, cached documents |

---

## File Discovery and Indexing Pipeline

```
User selects folder
        │
        ▼
┌─────────────────┐
│  Permission     │──▶ Verify read access to directory
│  check          │
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  Recursive scan │──▶ walkdir / os.walk
│  (file types)   │──▶ Filter by allowed extensions
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  Metadata extract│──▶ Size, dates, MIME type (filetype)
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  Store in DB    │──▶ PostgreSQL (metadata table)
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  OCR pipeline   │──▶ PaddleOCR (primary) / Tesseract (fallback)
│  (if scanned)   │──▶ Persian language model (fa)
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  Chunk + embed  │──▶ sentence-transformers (Persian model)
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  Store vectors  │──▶ pgvector (PostgreSQL)
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  Index complete │──▶ Notify user via system tray
└─────────────────┘
```

---

## Security Model

| Aspect | Implementation |
|--------|---------------|
| Code signing | EV certificate; MSI signed before distribution |
| Data encryption | Local database encryption at rest (SQLCipher or PostgreSQL TDE) |
| File access | User-authorized directories only; no silent scanning |
| File operations | Explicit user confirmation before move/delete/rename |
| Telemetry | Opt-in only; no data collection by default |
| Local processing | OCR, embeddings, AI inference run locally by default |
| Cloud AI | Optional; user must configure API key and consent |

---

## Build and Packaging

```
Development:
  cargo build (Rust backend)
  npm run dev (frontend)
  python -m uvicorn app.main:app (Python backend)

Production:
  cargo tauri build (bundles everything)
  → produces BARGEHAM_Setup.exe and BARGEHAM_Setup.msi
  → code-sign with EV certificate
  → publish to website / GitHub releases
```

---

## Performance Considerations

| Concern | Mitigation |
|---------|-----------|
| Large file indexing | Process in batches; show progress; don't block UI |
| Memory usage | Stream PDFs page-by-page; don't load whole files |
| OCR speed | Run on background thread; GPU acceleration if available |
| Database size | Vacuum PostgreSQL periodically; archive old indexes |
| Initial scan time | Incremental indexing; watch new files only after initial scan |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Windows Defender false positive | Medium | High | Code signing; submit to Microsoft for analysis |
| Large installer size | Low | Medium | Tauri small binary; optional components |
| Python dependency conflicts | Medium | Medium | Embed Python via PyO3 or use static builds |
| OCR accuracy on Persian documents | Medium | High | Test with real Persian documents; allow user correction |
| File system watcher misses events | Low | Medium | Periodic re-scan as fallback |

---

## Sources

- Tauri 2: https://tauri.app/ (MIT/Apache-2.0)
- watchdog: https://github.com/gorakhargosh/watchdog (Apache-2.0)
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR (Apache-2.0)
- Tesseract: https://tesseract-ocr.github.io/tessdoc/ (Apache-2.0)
- pgvector: https://github.com/pgvector/pgvector (MIT)
- Ollama: https://github.com/ollama/ollama (MIT)
- sentence-transformers: https://github.com/UKPLab/sentence-transformers (MIT)
- Persian embedding: https://huggingface.co/Msobhi/Persian_Sentence_Embedding_v3
- ReadDirectoryChangesW: Microsoft Windows API documentation
