# Report F — Persian AI and OCR Assessment

**Product:** BARGEHAM — Intelligent file/document management platform  
**Constraint:** Persian support is a CORE requirement, not optional  
**Status:** Research report — verified against HuggingFace model cards, GitHub repositories, official documentation  
**Distinction:** Verified facts vs. assumptions are clearly marked

---

## Executive Summary

Persian language support is achievable but requires careful component selection:

- **OCR:** PaddleOCR PP-OCRv5 with `arabic_PP-OCRv5_mobile_rec` model supports Persian (`fa`) — verified. Tesseract with `fas` language pack — available but quality unverified for Persian specifically.
- **Embeddings:** `Msobhi/Persian_Sentence_Embedding_v3` on HuggingFace — Persian-specific model available. Multilingual alternatives (BGE-m3, LaBSE) verified to include Persian.
- **Text normalization:** `arabic-reshaper` + `python-bidi` for RTL rendering; `python-persian-reshaper` for Persian-specific reshaping; ZWNJ/half-space and numeral normalization require custom code.
- **Full-text search:** Persian stemming/tokenization is a gap — PostgreSQL FTS has no built-in Persian config; custom tokenizer needed.
- **Persian PDF extraction:** pdfplumber can extract embedded text from Persian PDFs; scanned Persian PDFs need OCR first.

---

## 1. Persian OCR Quality and Engines

### Tesseract with Persian (fas) language pack

| Aspect | Status |
|--------|--------|
| Language code | `fas` (verified in Debian package `tesseract-ocr-fas`) |
| Tesseract version | 4.x+ supports LSTM-based OCR; Persian support added in 4.0 |
| Quality | **Unverified for Persian specifically** — no independent accuracy benchmark found |
| Installation | `apt install tesseract-ocr-fas` (Linux); `tesseract-ocr-fas` Windows binary available |
| Integration | `pytesseract` Python wrapper (MIT) |

Sources: [Debian tesseract-ocr-fas package](https://packages.debian.org/sid/tesseract-ocr-fas), [Tesseract language data](https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html)

### PaddleOCR with Persian (fa) support

| Aspect | Status |
|--------|--------|
| Model | `arabic_PP-OCRv5_mobile_rec` — covers Arabic, Persian, Uyghur, Urdu, Pashto, Kurdish, Sindhi, Balochi, English |
| Language code | `fa` |
| Accuracy | PaddleOCR reports 80-94% on Arabic script datasets; **specific Persian accuracy not independently verified** |
| Version | PP-OCRv5 (latest as of 2026) |
| Android | Community demos exist (Paddle Lite); no official Android SDK |
| Integration | Python package `paddleocr` (Apache-2.0) |

Sources: [PaddleOCR PP-OCRv5 multi-language docs](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.en.md)

### Other Persian OCR projects

| Project | URL | Status | Notes |
|---------|-----|--------|-------|
| FarsiOCR | https://github.com/stafazzoli/FarsiOCR | GitHub repo | OCR application for Farsi/Persian; activity unclear |
| Persian-OCR | https://github.com/sepehrraisi/Persian-OCR | GitHub repo | "A project to bring high accuracy OCR to Persian language"; activity unclear |
| FarsiOCR (web) | https://farsiocr.ir/ | Web service | Online Persian OCR; not local |
| IronOCR (Persian) | https://ironsoftware.com/ocr/csharp/languages/persian/ | Commercial | .NET OCR with Persian support; proprietary |

**Verdict:** Use **PaddleOCR** as primary OCR engine (Persian support confirmed, Apache-2.0, active maintenance). Use **Tesseract + fas** as fallback. Avoid unmaintained Persian-specific OCR projects (activity unclear).

---

## 2. Arabic/Persian Character Normalization

### Libraries

| Library | URL | License | Purpose | Platform |
|---------|-----|---------|---------|----------|
| arabic-reshaper | https://pypi.org/project/arabic-reshaper/ | MIT | Reconstruct Arabic sentences for correct display | Python (Windows+Android) |
| python-bidi | https://github.com/baoboa/pybidi | BSD | Bidirectional text algorithm | Python (Windows+Android) |
| python-persian-reshaper | https://github.com/ghaffaribehdad/python-persian-reshaper | MIT | Persian-specific text reshaping | Python (Windows+Android) |
| PersianConverter | https://pypi.org/project/PersianConverter/ | Unknown | Persian text conversion | Python |

### ZWNJ and Half-Space Handling

Persian uses Zero-Width Non-Joiner (U+200C) for half-spaces. This creates challenges:

- **Search:** "کتابخوانی" vs "کتاب خوانی" (with/without ZWNJ) should match the same
- **Sorting:** ZWNJ affects sort order
- **Display:** ZWNJ controls character joining in Persian script

**Required custom code:**
1. Unicode normalization (NFC/NFD) before comparison
2. ZWNJ-aware tokenization (treat ZWNJ as word boundary or ignore it based on context)
3. Half-space normalization (optional: convert ZWNJ to regular space for search)

### Persian/Arabic Numeral Normalization

Persian numerals (٠١٢٣٤٥٦٧٨٩) differ from Arabic-Indic numerals and Western numerals (0123456789). Required mapping:

| Persian | Arabic-Indic | Western |
|---------|-------------|---------|
| ۰ | ٠ | 0 |
| ۱ | ١ | 1 |
| ۲ | ٢ | 2 |
| ۳ | ٣ | 3 |
| ۴ | ٤ | 4 |
| ۵ | ٥ | 5 |
| ۶ | ٦ | 6 |
| ۷ | ٧ | 7 |
| ۸ | ٨ | 8 |
| ۹ | ٩ | 9 |

**Verdict:** Use `arabic-reshaper` + `python-bidi` for RTL display; custom normalization functions for ZWNJ, half-spaces, and numerals.

---

## 3. Mixed Persian-English Search

### Full-Text Search Options

| Option | Persian Support | Notes |
|--------|----------------|-------|
| PostgreSQL FTS | ⚠️ Partial | No built-in Persian dictionary/stemmer; requires custom text search config |
| SQLite FTS5 | ⚠️ Partial | Tokenizer is whitespace-based; no Persian stemming |
| Elasticsearch | ✅ | Persian analysis plugin available (community) |
| Meilisearch | ⚠️ Partial | Language detection; Persian support limited |
| Tantivy | ⚠️ Partial | Rust full-text; Persian tokenizer needed |

**Verdict:** For Windows desktop, use PostgreSQL FTS with custom Persian configuration OR rely on semantic search (vector) as primary, FTS as secondary. For Android, use SQLite FTS5 with custom tokenizer.

### Semantic Search for Persian+English

| Model | URL | Persian Support | Notes |
|-------|-----|----------------|-------|
| Msobhi/Persian_Sentence_Embedding_v3 | https://huggingface.co/Msobhi/Persian_Sentence_Embedding_v3 | ✅ Persian-specific | Sentence transformer for Persian |
| Sinaof1381/Persian_Sentence_Embedding | https://huggingface.co/Sinaof1381/Persian_Sentence_Embedding | ✅ Persian-specific | Alternative Persian embedding |
| BAAI/bge-m3 | https://huggingface.co/BAAI/bge-m3 | ✅ Multilingual (includes Persian) | 100+ languages; good for mixed Persian-English |
| sentence-transformers/LaBSE | https://huggingface.co/sentence-transformers/LaBSE | ✅ Cross-lingual | 109 languages; includes Persian |

**Verdict:** Use `Msobhi/Persian_Sentence_Embedding_v3` for Persian-specific embedding. Use `BAAI/bge-m3` for mixed Persian-English semantic search. Both loadable via `sentence-transformers` library.

---

## 4. RTL User Interface

### Desktop (Windows)

| Framework | RTL Support | Notes |
|-----------|------------|-------|
| Tauri 2 (webview) | ✅ | CSS `direction: rtl`; `rtl:` Tailwind variant |
| .NET (WPF/WinUI 3) | ✅ | `FlowDirection=RightToLeft` |
| Qt | ✅ | `layoutDirection` property |
| Electron | ✅ | CSS direction |

### Android

| Framework | RTL Support | Notes |
|-----------|------------|-------|
| Jetpack Compose | ✅ | `LayoutDirection.Rtl`; `LocalLayoutDirection` |
| Android Views | ✅ | `android:layoutDirection="rtl"` |
| Flutter | ✅ | `Directionality` widget |

**Verdict:** Use `dir="rtl"` and `lang="fa"` on HTML root element for webview-based desktop; `LayoutDirection.Rtl` for Compose. Use Persian fonts (Vazir, Iran Sans, or system Persian fonts).

---

## 5. Persian Document Extraction

### PDF Text Extraction (embedded text)

| Library | Persian Support | Notes |
|---------|----------------|-------|
| pdfplumber | ✅ | Extracts embedded text; works if PDF has text layer |
| PyMuPDF (fitz) | ✅ | Good Unicode support; Persian text extraction |
| pypdf | ✅ | Basic text extraction; may struggle with complex Persian fonts |

**Challenge:** Many Persian PDFs use non-standard font encodings. Extracted text may have garbled characters. OCR fallback needed for scanned/image-based Persian PDFs.

### Table Extraction from Persian Documents

| Library | Persian Support | Notes |
|---------|----------------|-------|
| pdfplumber | ✅ | Table detection works on layout; Persian text in cells may need post-processing |
| camelot | ⚠️ | PDF table extraction; Persian text handling untested |
| Tabula | ⚠️ | Java-based; Persian support unknown |

**Verdict:** Use pdfplumber for text + table extraction; OCR fallback for scanned documents; verify Persian font encoding handling.

---

## 6. Persian Document Embeddings

### Model Comparison

| Model | URL | Size | Persian Quality | Multilingual | License |
|-------|-----|------|-----------------|--------------|---------|
| Msobhi/Persian_Sentence_Embedding_v3 | HF | ~110MB | ✅ Persian-specific | ❌ Persian only | HF license |
| Sinaof1381/Persian_Sentence_Embedding | HF | ~110MB | ✅ Persian-specific | ❌ Persian only | HF license |
| BAAI/bge-m3 | HF | ~560MB | ✅ Good | ✅ 100+ languages | MIT |
| sentence-transformers/LaBSE | HF | ~580MB | ✅ Good | ✅ 109 languages | Apache-2.0 |

**Verdict:** Use `Msobhi/Persian_Sentence_Embedding_v3` for Persian-only search. Use `BAAI/bge-m3` for mixed Persian-English queries.

---

## 7. Practical Recommendations for BARGEHAM

### Persian Stack

| Component | Recommendation | License | Verified Persian Support |
|-----------|---------------|---------|-------------------------|
| OCR | PaddleOCR PP-OCRv5 (`fa`) | Apache-2.0 | ✅ (80-94% on Arabic script; Persian-specific unverified) |
| OCR fallback | Tesseract + `fas` | Apache-2.0 | ⚠️ (language pack available; quality unverified) |
| Embeddings | Msobhi/Persian_Sentence_Embedding_v3 | HF | ✅ (Persian-specific) |
| Multilingual embeddings | BAAI/bge-m3 | MIT | ✅ (includes Persian) |
| RTL rendering | arabic-reshaper + python-bidi | MIT/BSD | ✅ |
| Persian reshaping | python-persian-reshaper | MIT | ✅ |
| ZWNJ/half-space | Custom normalization | N/A | ⚠️ (needs implementation) |
| Numeral normalization | Custom mapping | N/A | ⚠️ (needs implementation) |
| Full-text search | PostgreSQL FTS + custom Persian config | PostgreSQL | ⚠️ (needs custom config) |
| Semantic search | pgvector + Persian embedding | MIT | ✅ |

### Implementation Priority

1. **P0:** PaddleOCR with Persian model + Msobhi embedding + RTL UI
2. **P1:** ZWNJ/half-space normalization + numeral normalization + Persian FTS config
3. **P2:** Mixed Persian-English semantic search (bge-m3) + Persian document classification fine-tuning

---

## Sources

- PaddleOCR Persian support: https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.en.md
- Tesseract fas package: https://packages.debian.org/sid/tesseract-ocr-fas
- Tesseract language data: https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html
- Msobhi Persian embedding: https://huggingface.co/Msobhi/Persian_Sentence_Embedding_v3
- Sinaof1381 Persian embedding: https://huggingface.co/Sinaof1381/Persian_Sentence_Embedding
- BGE-m3: https://huggingface.co/BAAI/bge-m3
- LaBSE: https://huggingface.co/sentence-transformers/LaBSE
- arabic-reshaper: https://pypi.org/project/arabic-reshaper/ (MIT)
- python-bidi: https://github.com/baoboa/pybidi (BSD)
- python-persian-reshaper: https://github.com/ghaffaribehdad/python-persian-reshaper (MIT)
- FarsiOCR: https://github.com/stafazzoli/FarsiOCR
- Persian-OCR: https://github.com/sepehrraisi/Persian-OCR
- IronOCR Persian: https://ironsoftware.com/ocr/csharp/languages/persian/
