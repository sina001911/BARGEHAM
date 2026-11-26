# Report B — Feature Comparison Matrix

**Product:** BARGEHAM — Intelligent file/document management platform  
**Constraint:** Native Windows desktop (EXE/MSI) + native Android companion (APK/AAB)  
**Status:** Research report — verified against official documentation and repositories

---

## Feature Dimensions

| Dimension | Description |
|-----------|-------------|
| **Native Windows** | Installable EXE/MSI, not web-based |
| **Native Android** | Installable APK/AAB, not mobile website/PWA |
| **Offline/Local-first** | Core features work without internet; local processing default |
| **File Discovery** | Scan user-authorized directories, identify file types/metadata |
| **Duplicate Detection** | Find duplicate and similar files |
| **OCR** | Extract text from scanned documents/images |
| **Document Classification** | Auto-categorize documents (contracts, invoices, reports, etc.) |
| **Semantic Search** | Vector-based meaning search across documents |
| **RAG AI Assistant** | Chat with documents, cited answers with page references |
| **Automatic Classification** | Recommend folder structures, naming improvements |
| **Intelligent Recommendations** | Detect org problems, missing docs, storage inefficiencies |
| **Persian Language** | Persian OCR, RTL UI, Persian embeddings, mixed Persian-English search |
| **Explicit User Approval** | No file moves/deletes without user consent |
| **Android Scoped Storage** | Respects Android storage restrictions (SAF, MediaStore) |
| **Windows–Android Sync** | Secure connection between desktop and mobile |
| **Background Processing** | Indexing/monitoring without blocking UI |
| **License** | Open source vs proprietary |

---

## Feature Comparison Matrix

| Feature | BARGEHAM (target) | AnythingLLM | Paperless-ngx | Eagle | DEVONthink | Khoj | NotebookLM | TagSpaces | File Juggler | Hazel |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Native Windows | ✅ | ✅ | ❌ | ✅ | ❌ | ⚠️ | ❌ | ✅ | ✅ | ❌ |
| Native Android | ✅ | ✅ | ⚠️ | ❌ | ❌ | ⚠️ | ❌ | ✅ | ❌ | ❌ |
| Offline / Local-first | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| File Discovery | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ |
| Duplicate Detection | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| OCR | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Document Classification | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Semantic Search | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ✅ | ❌ | ❌ | ❌ |
| RAG AI Assistant | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Automatic Classification | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ⚠️ | ✅ |
| Intelligent Recommendations | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Persian Language | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ |
| Explicit User Approval | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Android Scoped Storage | ✅ | ⚠️ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ⚠️ | ❌ | ❌ |
| Windows–Android Sync | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Background Processing | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ | ⚠️ | ⚠️ | ⚠️ |
| License | TBD | MIT | AGPL-3.0 | Proprietary | Proprietary | AGPL-3.0 | Proprietary | AGPL-3.0 | Proprietary | Proprietary |

**Legend:** ✅ = Supported, ❌ = Not supported, ⚠️ = Partial/limited/unofficial

---

## Common Features (Already Implemented by Competitors)

These features exist in at least one competitor product:

1. **Native Windows desktop app** — Eagle, File Juggler, AnythingLLM, TagSpaces
2. **Native Android app** — AnythingLLM, TagSpaces (third-party APK)
3. **Offline/local-first** — AnythingLLM, Paperless-ngx, Eagle, DEVONthink, Khoj, TagSpaces, File Juggler, Hazel
4. **OCR** — Paperless-ngx, DEVONthink
5. **Semantic search** — AnythingLLM, Eagle, Khoj, NotebookLM
6. **RAG AI assistant** — AnythingLLM, Paperless-ngx (optional), DEVONthink, Khoj, NotebookLM
7. **Document classification** — Paperless-ngx, Eagle, DEVONthink, File Juggler, Hazel
8. **Duplicate detection** — Eagle
9. **Tagging/folder organization** — Eagle, DEVONthink, Hazel, TagSpaces, File Juggler

---

## Missing Features (Gap Analysis — BARGEHAM Differentiation Opportunities)

These features are **missing from ALL competitors** or poorly implemented:

| Missing Feature | BARGEHAM Opportunity |
|-----------------|---------------------|
| Native Windows + Native Android together | AnythingLLM comes close but is the only one; most are desktop-only or web-only |
| Local-first AI + OCR + Persian | No competitor combines all three |
| Persian OCR (Tesseract fas + PaddleOCR fa) | Zero competitors have native Persian OCR |
| Persian RTL UI | Zero competitors have Persian RTL interface |
| Persian sentence embeddings | Zero competitors have Persian vector search |
| Mixed Persian-English search | Zero competitors support mixed-language queries |
| Explicit user approval before file operations | Zero competitors require consent before move/delete |
| Intelligent recommendations (org problems, missing docs, storage inefficiencies) | Zero competitors provide proactive org insights |
| Windows–Android secure sync | AnythingLLM has this; others don't |
| Background file monitoring on Windows | Limited implementation across competitors |
| Android scoped storage compliance | Most Android-capable apps don't address this explicitly |

---

## Feature Maturity Assessment

| Feature | Market Maturity | BARGEHAM Difficulty | Differentiation Potential |
|---------|:---:|:---:|:---:|
| Native Windows desktop | High | Low | Low |
| Native Android | Medium | Medium | Medium |
| Local-first processing | Medium | Medium | High |
| OCR (English) | High | Low | Low |
| OCR (Persian) | Low | High | **Very High** |
| Semantic search | High | Low | Medium |
| RAG AI assistant | High | Medium | Medium |
| Document classification | Medium | Medium | Medium |
| Duplicate detection | Medium | Low | Low |
| Persian RTL UI | Low | Medium | **Very High** |
| Intelligent recommendations | Low | High | **Very High** |
| Explicit user approval | Low | Low | **High** |
| Windows–Android sync | Medium | Medium | High |
| Android scoped storage | Low | High | Medium |

---

## Sources

- AnythingLLM: https://anythingllm.com/download
- Paperless-ngx: https://github.com/paperless-ngx/paperless-ngx
- Eagle: https://en.eagle.cool/
- DEVONthink: https://alternativeto.net/software/devonthink/about/
- Hazel: https://alternativeto.net/software/hazel/
- File Juggler: https://www.filejuggler.com/
- Khoj: https://github.com/khoj-ai/khoj
- NotebookLM: https://labs.google.com/search/experiment/23
- DocFetcher: https://docfetcher.sourceforge.io/
- TagSpaces: https://github.com/tagspaces/tagspaces
