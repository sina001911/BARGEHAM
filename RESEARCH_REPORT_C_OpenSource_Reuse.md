# Report C — Open-Source Reuse Opportunities

**Product:** BARGEHAM — Intelligent file/document management platform  
**Constraint:** Native Windows desktop (EXE/MSI) + native Android companion (APK/AAB)  
**Status:** Research report — verified against GitHub repositories, PyPI, official documentation  
**Rule:** Never recommend copying code without reviewing its license

---

## Executive Summary

BARGEHAM should reuse battle-tested open-source libraries for: file system monitoring (watchdog), OCR (Tesseract + PaddleOCR), document parsing (pdfplumber, python-docx), vector search (pgvector, sqlite-vec), embeddings (sentence-transformers, Persian models), local LLM inference (Ollama), and RTL text processing (arabic-reshaper, python-bidi). Complete applications (Paperless-ngx, AnythingLLM, Khoj) should be studied but not forked due to license (AGPL-3.0) and architecture mismatch (web/Docker vs native desktop).

---

## Reuse Recommendations by Category

### 1. File Indexing

| Component | Recommendation | License | Windows | Android | Notes |
|-----------|---------------|---------|---------|---------|-------|
| File system monitoring | **watchdog** (Python) | Apache-2.0 | ✅ | ❌ | Cross-platform file watching; Windows uses ReadDirectoryChangesW via Python bindings |
| Directory scanning | Custom (Python os.walk / pathlib) | N/A | ✅ | ✅ | Simple recursive scan; no library needed |
| File type detection | **python-magic** (libmagic bindings) | MIT | ✅ | ⚠️ | Requires libmagic binary; Android needs prebuilt .so |
| MIME detection | **filetype** (Python) | MIT | ✅ | ✅ | Pure Python, no system dependencies |

**Verdict:** Reuse watchdog for Windows file monitoring; custom Python for scanning; filetype for MIME detection.

**Sources:**
- watchdog: https://github.com/gorakhargosh/watchdog (Apache-2.0, actively maintained, last release 2024)
- filetype: https://github.com/h2non/filetype.py (MIT)

---

### 2. OCR

| Component | Recommendation | License | Windows | Android | Notes |
|-----------|---------------|---------|---------|---------|-------|
| Primary OCR engine | **PaddleOCR** (PP-OCRv5) | Apache-2.0 | ✅ | ✅ (mobile demo) | Supports Persian via arabic_PP-OCRv5_mobile_rec model (Arabic, Persian, Uyghur, Urdu, Pashto, Kurdish, Sindhi, Balochi, English) |
| Fallback OCR | **Tesseract** + fas language pack | Apache-2.0 | ✅ | ⚠️ (tess-two unmaintained) | Tesseract 4+ supports Persian; tess-two (Android) is unmaintained |
| PDF text layer | **pdfplumber** | MIT | ✅ | ⚠️ | Extracts embedded text from PDFs without OCR |
| Image preprocessing | **Pillow + OpenCV** | MIT / Apache-2.0 | ✅ | ✅ | Image enhancement before OCR |

**Verdict:** Use PaddleOCR as primary (Persian support confirmed), Tesseract as fallback. On Android, use ML Kit bundled (Google-maintained, offline) instead of tess-two.

**Persian OCR quality:** PaddleOCR reports 80-94% accuracy on Arabic script datasets; specific Persian accuracy not independently verified. Tesseract fas pack quality varies by document quality.

**Sources:**
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR (Apache-2.0, PP-OCRv5 supports Persian "fa")
- Tesseract: https://tesseract-ocr.github.io/tessdoc/ (Apache-2.0, fas language pack available)
- ML Kit Android: https://developers.google.com/ml-kit/vision/text-recognition/v2/android

---

### 3. Document Parsing

| Component | Recommendation | License | Windows | Android | Notes |
|-----------|---------------|---------|---------|---------|-------|
| PDF text extraction | **pdfplumber** | MIT | ✅ | ⚠️ | Good table extraction; pure Python |
| PDF rendering | **PdfiumAndroid** / PdfRenderer | Apache-2.0 | N/A | ✅ | Android framework API (API 21+); renders pages one at a time |
| DOCX parsing | **python-docx** | MIT | ✅ | ⚠️ | Pure Python; Android needs Java equivalent |
| XLSX parsing | **openpyxl** | MIT | ✅ | ⚠️ | Pure Python; Android needs Java equivalent |
| TXT / plain text | Custom (Python) | N/A | ✅ | ✅ | Simple file read |

**Verdict:** Use pdfplumber + python-docx + openpyxl for Windows backend. On Android, use PdfRenderer/Pdfium for PDFs and custom parsers for other formats.

**Sources:**
- pdfplumber: https://github.com/jsvine/pdfplumber (MIT)
- python-docx: https://github.com/python-openxml/python-docx (MIT)
- openpyxl: https://foss.heptapod.net/openpyxl/openpyxl (MIT)
- PdfRenderer: https://developer.android.com/reference/kotlin/android/graphics/pdf/PdfRenderer

---

### 4. Document Classification

| Component | Recommendation | License | Windows | Android | Notes |
|-----------|---------------|---------|---------|---------|-------|
| Zero-shot classification | **sentence-transformers** + NLI model | MIT | ✅ | ⚠️ | Classify documents into categories without training |
| Fine-tuned classification | **scikit-learn** + TF-IDF | BSD-3 | ✅ | ⚠️ | Train on labeled document samples |
| Persian-specific | Custom fine-tuning on Persian data | N/A | ✅ | ⚠️ | Requires Persian training data |

**Verdict:** Use sentence-transformers zero-shot classification for initial deployment; fine-tune on Persian-labeled data later.

**Sources:**
- sentence-transformers: https://github.com/UKPLab/sentence-transformers (MIT)
- scikit-learn: https://github.com/scikit-learn/scikit-learn (BSD-3)

---

### 5. Vector Search

| Component | Recommendation | License | Windows | Android | Notes |
|-----------|---------------|---------|---------|---------|-------|
| Embedded vector DB | **pgvector** (PostgreSQL extension) | MIT | ✅ | ❌ | Requires PostgreSQL server; good for Windows desktop with local DB |
| Mobile vector search | **sqlite-vec** | MIT | ✅ | ✅ | Pure C, runs anywhere SQLite runs; pre-v1 (breaking changes expected) |
| In-memory index | **FAISS** | MIT | ✅ | ⚠️ | Facebook AI Similarity Search; Android needs JNI bindings |
| Vector DB server | **Qdrant** | Apache-2.0 | ✅ | ❌ | REST/gRPC API; server required |

**Verdict:** Use pgvector for Windows desktop (with local PostgreSQL). Use sqlite-vec for Android (via NDK). Avoid FAISS on Android (JNI complexity).

**Sources:**
- pgvector: https://github.com/pgvector/pgvector (MIT)
- sqlite-vec: https://github.com/asg017/sqlite-vec (MIT, pre-v1)
- Qdrant: https://github.com/qdrant/qdrant (Apache-2.0)

---

### 6. Full-Text Search

| Component | Recommendation | License | Windows | Android | Notes |
|-----------|---------------|---------|---------|---------|-------|
| SQLite FTS5 | Built-in | Public Domain | ✅ | ✅ | Full-text search in SQLite; no extra dependency |
| PostgreSQL FTS | Built-in | PostgreSQL License | ✅ | ❌ | With pgvector deployment |
| Meilisearch | AGPL-3.0 | ❌ | ❌ | Server required |
| Tantivy | Apache-2.0 | ✅ | ❌ | Rust full-text search engine |

**Verdict:** Use SQLite FTS5 for Android; PostgreSQL FTS for Windows desktop.

---

### 7. RAG (Retrieval-Augmented Generation)

| Component | Recommendation | License | Windows | Android | Notes |
|-----------|---------------|---------|---------|---------|-------|
| RAG framework | **LangChain** or **LlamaIndex** | MIT | ✅ | ⚠️ | Python frameworks for RAG pipelines |
| Local LLM server | **Ollama** | MIT | ✅ | ❌ | Windows desktop API server; models run locally |
| LLM inference | **llama.cpp** | MIT | ✅ | ✅ (Android port exists) | C++ inference engine; Android needs NDK build |
| ONNX Runtime | **onnxruntime** | MIT | ✅ | ✅ | Official Android AAR; NNAPI/CPU/QNN providers |

**Verdict:** Use Ollama for Windows desktop LLM inference. Use ONNX Runtime Mobile or llama.cpp Android port for on-device AI on Android.

**Sources:**
- LangChain: https://github.com/langchain-ai/langchain (MIT)
- Ollama: https://github.com/ollama/ollama (MIT, Windows support confirmed)
- ONNX Runtime: https://github.com/microsoft/onnxruntime (MIT, Android AAR available)
- llama.cpp: https://github.com/ggerganov/llama.cpp (MIT)

---

### 8. Local AI Inference

| Component | Recommendation | License | Windows | Android | Notes |
|-----------|---------------|---------|---------|---------|-------|
| LLM runtime | **Ollama** | MIT | ✅ | ❌ | Easy model management, API server |
| Embedding model | **sentence-transformers** | MIT | ✅ | ⚠️ | Persian model: Msobhi/Persian_Sentence_Embedding_v3 |
| Multilingual embedding | **BGE-m3** or **LaBSE** | MIT / Apache-2.0 | ✅ | ✅ | Mixed Persian-English search |
| ONNX Runtime | **onnxruntime** | MIT | ✅ | ✅ | Hardware acceleration (NNAPI on Android) |

**Persian embedding models:**
- Msobhi/Persian_Sentence_Embedding_v3 (HuggingFace) — Persian-specific
- Sinaof1381/Persian_Sentence_Embedding (HuggingFace) — Persian-specific
- BGE-m3 (BAAI/bge-m3) — Multilingual, includes Persian
- LaBSE (sentence-transformers/LaBSE) — Cross-lingual

**Verdict:** Use Ollama for LLM, sentence-transformers with Persian model for embeddings.

**Sources:**
- Ollama: https://github.com/ollama/ollama
- Persian embedding: https://huggingface.co/Msobhi/Persian_Sentence_Embedding_v3
- BGE-m3: https://huggingface.co/BAAI/bge-m3

---

### 9. Duplicate Detection

| Component | Recommendation | License | Windows | Android | Notes |
|-----------|---------------|---------|---------|---------|-------|
| Exact duplicates | **SHA-256 hashing** | N/A | ✅ | ✅ | Cryptographic hash; zero false positives |
| Near duplicates | **ssdeep** (fuzzy hashing) | GPL-2.0 | ✅ | ⚠️ | Context-triggered piecewise hashing |
| Perceptual duplicates | **pdqhash** / **ImageHash** | Various | ✅ | ✅ | For image/document visual duplicates |
| Content similarity | **MinHash + LSH** | N/A | ✅ | ✅ | Custom implementation |

**Verdict:** Use SHA-256 for exact duplicates; implement MinHash+LSH for near-duplicate text documents; avoid ssdeep (GPL-2.0 is viral).

**Sources:**
- ssdeep: https://github.com/ssdeep-project/ssdeep (GPL-2.0)
- ImageHash: https://github.com/JohannesBuchner/imagehash

---

### 10. File Monitoring (Windows)

| Component | Recommendation | License | Windows | Android | Notes |
|-----------|---------------|---------|---------|---------|-------|
| File system events | **watchdog** | Apache-2.0 | ✅ | ❌ | Uses ReadDirectoryChangesW on Windows |
| Directory change polling | Custom (polling) | N/A | ✅ | ✅ | Fallback when watchdog unavailable |

**Verdict:** Use watchdog for Windows; polling fallback for Android.

---

### 11. RTL Text Processing (Persian)

| Component | Recommendation | License | Windows | Android | Notes |
|-----------|---------------|---------|---------|---------|-------|
| Arabic/Persian reshaping | **arabic-reshaper** | MIT | ✅ | ✅ | Pure Python; also available as Kotlin/Java port |
| Bidirectional text | **python-bidi** | BSD | ✅ | ✅ | Pure Python |
| Persian normalizer | **python-persian-reshaper** | MIT | ✅ | ✅ | GitHub: ghaffaribehdad/python-persian-reshaper |
| ZWNJ / half-space handling | Custom normalization | N/A | ✅ | ✅ | Unicode normalization + custom rules |
| Persian numerals | Custom mapping | N/A | ✅ | ✅ | ٠١٢٣٤٥٦٧٨٩ → 0123456789 |

**Verdict:** Use arabic-reshaper + python-bidi for text rendering; custom normalization for ZWNJ and numerals.

**Sources:**
- arabic-reshaper: https://pypi.org/project/arabic-reshaper/ (MIT)
- python-bidi: https://github.com/baoboa/pybidi (BSD)
- Persian reshaper: https://github.com/ghaffaribehdad/python-persian-reshaper (MIT)

---

### 12. Cross-Device Synchronization

| Component | Recommendation | License | Windows | Android | Notes |
|-----------|---------------|---------|---------|---------|-------|
| Cloud relay | Custom (gRPC/REST) | N/A | ✅ | ✅ | BARGEHAM-operated sync server |
| Local sync | **Syncthing** | MPL-2.0 | ✅ | ⚠️ | Official Android app discontinued; community forks exist |
| CRDT sync | **Automerge** | MIT | ✅ | ✅ | JSON-like data structures with automatic merging |

**Verdict:** Build custom sync server (cloud relay) with offline-first queue. Avoid Syncthing (official Android app discontinued Dec 2024). Consider Automerge for conflict-free document state.

**Sources:**
- Syncthing: https://github.com/syncthing/syncthing-android (discontinued)
- Automerge: https://github.com/automerge/automerge (MIT)

---

## Reuse vs Build Decision Matrix

| Category | Reuse Open-Source | Adapt | Build Independently | Reason |
|----------|:---:|:---:|:---:|--------|
| File indexing | watchdog | — | — | Mature, Apache-2.0, Windows support |
| File type detection | filetype | — | — | Pure Python, MIT |
| OCR | PaddleOCR + Tesseract | — | — | Persian support confirmed, Apache-2.0 |
| PDF parsing | pdfplumber | — | — | MIT, good table extraction |
| DOCX/XLSX parsing | python-docx + openpyxl | — | — | MIT, pure Python |
| Document classification | sentence-transformers | Fine-tune on Persian | — | Zero-shot works out of box |
| Vector search | pgvector (Win) + sqlite-vec (Android) | — | — | pgvector MIT; sqlite-vec pre-v1 risk |
| Full-text search | SQLite FTS5 + PostgreSQL FTS | — | — | Built-in, no extra dependency |
| RAG | LangChain / LlamaIndex | — | — | MIT, Python-native |
| LLM inference | Ollama | — | — | Windows confirmed, MIT |
| Embeddings | sentence-transformers (Persian model) | — | — | Msobhi Persian model on HF |
| Duplicate detection | SHA-256 + custom MinHash | — | — | GPL libraries avoided |
| RTL processing | arabic-reshaper + python-bidi | — | — | MIT/BSD, pure Python |
| Sync | Custom server | — | — | Syncthing Android discontinued |
| Desktop UI framework | Tauri 2 / .NET / Qt | — | — | To be selected in Report D |

---

## License Compliance Summary

| License | Viral? | Can use in proprietary? | BARGEHAM recommendation |
|---------|--------|------------------------|------------------------|
| MIT | No | Yes | ✅ Safe for all components |
| Apache-2.0 | No | Yes | ✅ Safe for all components |
| BSD-3 | No | Yes | ✅ Safe for all components |
| AGPL-3.0 | Yes | No (must open source) | ❌ Avoid (Paperless-ngx, Khoj, TagSpaces) |
| GPL-2.0 | Yes | No (must open source) | ❌ Avoid (ssdeep) |
| MPL-2.0 | Weak | Yes (if modified files are open) | ⚠️ Caution (Syncthing) |

**Components to AVOID due to license:** Paperless-ngx (AGPL-3.0), Khoj (AGPL-3.0), ssdeep (GPL-2.0), TagSpaces (AGPL-3.0).

---

## Sources

- watchdog: https://github.com/gorakhargosh/watchdog
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- Tesseract: https://tesseract-ocr.github.io/tessdoc/
- pdfplumber: https://github.com/jsvine/pdfplumber
- python-docx: https://github.com/python-openxml/python-docx
- openpyxl: https://foss.heptapod.net/openpyxl/openpyxl
- sentence-transformers: https://github.com/UKPLab/sentence-transformers
- pgvector: https://github.com/pgvector/pgvector
- sqlite-vec: https://github.com/asg017/sqlite-vec
- Ollama: https://github.com/ollama/ollama
- ONNX Runtime: https://github.com/microsoft/onnxruntime
- Msobhi Persian embedding: https://huggingface.co/Msobhi/Persian_Sentence_Embedding_v3
- arabic-reshaper: https://pypi.org/project/arabic-reshaper/
- python-bidi: https://github.com/baoboa/pybidi
- Persian reshaper: https://github.com/ghaffaribehdad/python-persian-reshaper
- Automerge: https://github.com/automerge/automerge
- Syncthing Android (discontinued): https://github.com/syncthing/syncthing-android
