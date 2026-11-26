# Report E — Android Architecture: Storage, Background Processing, OCR, Sync

**Product:** BARGEHAM (intelligent document management platform — Windows Desktop + Android Mobile)  
**Status:** Research report — verified against developer.android.com and library documentation  
**Key warning:** BARGEHAM must NOT assume an Android app can freely scan the entire device. Android scoped storage (API 29+) explicitly prohibits arbitrary filesystem access.

---

## Executive Summary

On Android, a document-management app can only reliably reach:

1. Its own app-private directories (`getFilesDir()`, `getExternalFilesDir()`, `getCacheDir()`), deleted on uninstall.
2. Media the app itself created in MediaStore.
3. Images/video/audio created by *other* apps, via MediaStore + runtime permissions (`READ_MEDIA_IMAGES/VIDEO/AUDIO`, API 33+).
4. Specific files/folders the user explicitly picks through the system UI (Storage Access Framework / Photo Picker), optionally remembered across reboots via `takePersistableUriPermission()`.
5. Practically everything else — only via `MANAGE_EXTERNAL_STORAGE` ("All Files Access"), which requires a special system settings grant, is heavily scrutinized by Google Play (permitted uses include document managers, backup, on-device file search), and can be revoked by the user at any time.

Background continuous indexing is **not** reliably possible: Doze, App Standby buckets, battery-restriction settings, and OEM aggressive background killing all throttle or stop background work. A foreground service with a persistent notification (and, on API 34+, a foreground-service type + matching permission) is the only way to keep long-running indexing alive, and even that is killed by some OEMs unless the user whitelists the app.

Consequently, BARGEHAM on Android should be designed as: **user-picked folders/files + MediaStore media, offline-first local index, sync via cloud relay or periodic opportunistic background sync, OCR/indexing done on demand or while the app is in use (or via foreground service for large batches with explicit user consent).**

---

## 1. Android Storage Access Framework (SAF)

### How apps get user-authorized directory/file access

The Storage Access Framework (introduced API 19) lets a user pick documents or directories through a system-provided UI, so the app never needs a storage permission for that access:

| Intent | Purpose | Added |
|---|---|---|
| `ACTION_OPEN_DOCUMENT` | User picks one or more files; returns content:// URIs with persistable read/write grants | API 19 |
| `ACTION_OPEN_DOCUMENT_TREE` | User picks a directory tree; app gains access to the whole subtree | API 21 |
| `ACTION_CREATE_DOCUMENT` | User picks a location to create a new file | API 19 |

The caller sets acceptable MIME types (`setType`, `EXTRA_MIME_TYPES`) and must include `CATEGORY_OPENABLE` to obtain URIs openable via `ContentResolver.openFileDescriptor()`. Returned URIs are `content://` URIs backed by installed `DocumentsProvider` instances (local media, cloud-storage providers, etc.).  
Sources: [Intent.ACTION_OPEN_DOCUMENT](https://developer.android.com/reference/kotlin/android/content/Intent#ACTION_OPEN_DOCUMENT:kotlin.String), [Storage Access Framework training](https://developer.android.com/training/data-storage/shared/documents-files).

### DocumentFile, Uri, ContentResolver

- `DocumentFile` is a convenience wrapper over `DocumentsContract` exposing file-like operations (`getUri()`, `getName()`, `length()`, `lastModified()`, `isDirectory()`, `listFiles()`, `createFile()`, `delete()`, `renameTo()`).
- Under the hood, apps use `ContentResolver` to open streams (`openFileDescriptor(uri, mode)` / `openInputStream(uri)` / `openOutputStream(uri)`) and query `DocumentsContract.Document` metadata (MIME type, size, flags such as `FLAG_VIRTUAL_DOCUMENT`).
- SAF works across app boundaries: a `content://` URI can be shared so any receiver with the URI grant can open it.

### Persisted URI permissions (access across reboots)

URI grants from `ACTION_OPEN_DOCUMENT*` include persistable read/write permission, but they are **not** automatically remembered across reboots. The app must explicitly call:

```kotlin
contentResolver.takePersistableUriPermission(uri,
    Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
```

Once taken, the grant is remembered across device reboots (`ContentResolver.getPersistedUriPermissions()` lists them). Caveats verified in docs:

- Only URIs granted with `Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION` can be persisted.
- Access is **lost if the document is moved or deleted**; the app must re-acquire permission via the picker.

Sources: [ContentResolver.takePersistableUriPermission](https://developer.android.com/reference/kotlin/android/content/ContentResolver#takePersistableUriPermission(android.net.Uri,kotlin.Int)), [ACTION_OPEN_DOCUMENT reference](https://developer.android.com/reference/kotlin/android/content/Intent#ACTION_OPEN_DOCUMENT:kotlin.String), [SAF training](https://developer.android.com/training/data-storage/shared/documents-files).

**Implication for BARGEHAM:** store the user's chosen document-folder URIs (persisted) at setup; re-prompt if a folder is moved/deleted. Do not rely on hard-coded paths like `/sdcard/Documents`.

---

## 2. MediaStore

MediaStore is the system's media database (images, video, audio). Apps query collections via `ContentResolver.query()` against collection URIs such as `MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL)`.

### Accessible vs restricted file types

| Collection | Permission (targeting API 33+) | Notes |
|---|---|---|
| Images (own app's files) | None needed | App always accesses media it created |
| Images (other apps) | `READ_MEDIA_IMAGES` (dangerous, runtime) | Enforced API 33+ |
| Video (other apps) | `READ_MEDIA_VIDEO` | Enforced API 33+ |
| Audio (other apps) | `READ_MEDIA_AUDIO` | Enforced API 33+ |
| `MediaStore.Downloads` | Same media permissions by type | Downloads collection queryable like other collections |
| Non-media files (PDF, DOCX, ZIP, etc. in shared storage) | **Not accessible via MediaStore** | Requires SAF or `MANAGE_EXTERNAL_STORAGE` |

Legacy permissions:
- `READ_EXTERNAL_STORAGE` (API 16; enforced API 19+) — **no effect starting API 33** for media access; use `READ_MEDIA_*` instead.
- `WRITE_EXTERNAL_STORAGE` — only relevant with `android:maxSdkVersion="29"`; scoped storage makes it obsolete for most uses.

To delete media the app no longer owns on API 30+, use `MediaStore.createTrashRequest()` / `createDeleteRequest()` so the user chooses; catching `RecoverableSecurityException` per file is the older pattern.

Sources: [MediaStore training](https://developer.android.com/training/data-storage/shared/media), [READ_MEDIA_IMAGES](https://developer.android.com/reference/kotlin/android/Manifest.permission#READ_MEDIA_IMAGES), [READ_EXTERNAL_STORAGE](https://developer.android.com/reference/kotlin/android/Manifest.permission#READ_EXTERNAL_STORAGE).

### Photo picker (recommended for single-file selection)

`PickVisualMedia` / `PickMultipleVisualMedia` (AndroidX activity 1.7.0+) launches the system photo picker; no storage permissions required; falls back to `ACTION_OPEN_DOCUMENT` on API 19+ if the picker is unavailable. Android 14 (API 34) added `READ_MEDIA_VISUAL_USER_SELECTED` for partial-access ("selected photos") mode; Android 15 (API 35) adds `QUERY_ARG_LATEST_SELECTION_ONLY` to highlight recently selected items. Sources: [Photo Picker training](https://developer.android.com/training/data-storage/shared/photo-picker), [Android 15 features](https://developer.android.com/about/versions/15/features).

---

## 3. Scoped storage restrictions (Android 10 / API 29+)

### Core rule

Apps targeting API 29+ get **scoped access** to external storage by default: only their app-specific directory and media they created. Apps **cannot** access arbitrary filesystem paths or other apps' app-specific directories (`/sdcard/Android/data/&lt;other-package&gt;/...`).

### Version-by-version behavior

| Android | API | Scoped-storage behavior |
|---|---|---|
| 10 | 29 | Scoped storage default; `requestLegacyExternalStorage="true"` temporarily opts out in production |
| 11 | 30 | `requestLegacyExternalStorage` **ignored**; `MANAGE_EXTERNAL_STORAGE` added; All Files Access via settings |
| 12 | 31 | Scoped storage enforced; stricter background service/alarm rules (`SCHEDULE_EXACT_ALARM`) |
| 13 | 33 | `READ_MEDIA_IMAGES/VIDEO/AUDIO` replace `READ_EXTERNAL_STORAGE` for other apps' media; `READ_EXTERNAL_STORAGE` has no effect |
| 14 | 34 | Granular photo access (`READ_MEDIA_VISUAL_USER_SELECTED`); foreground-service types + per-type permissions required |
| 15 | 35 | `QUERY_ARG_LATEST_SELECTION_ONLY` for partial media access |

Sources: [Data storage training](https://developer.android.com/training/data-storage), [Android 15 features](https://developer.android.com/about/versions/15/features).

### MANAGE_EXTERNAL_STORAGE / All Files Access

- Added API 30. Protection level: `signature\|appop\|preinstalled`.
- Declaring it is **not enough**: the app must launch `Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION` (`package:&lt;app&gt;`) so the user toggles "Allow access to manage all files" in system settings. Check with `Environment.isExternalStorageManager()`.
- What it grants: read/write all shared-storage files, `MediaStore.Files` table, USB OTG/SD card roots, write to internal storage dirs except other apps' `/Android/data/`. Other apps' app-specific directories remain inaccessible.
- **Google Play policy (in effect since May 2021):** apps targeting API 30+ that declare this permission are evaluated; usage must be strictly necessary (no SAF/MediaStore alternative) and tied to core functionality. Permitted uses explicitly include **file managers, backup/restore, anti-virus, document management apps, on-device file search, disk/file encryption, device-to-device migration**. Apps outside these uses risk rejection, and the user can revoke the grant at any time.

Sources: [Manage all files training](https://developer.android.com/training/data-storage/manage-all-files), [MANAGE_EXTERNAL_STORAGE](https://developer.android.com/reference/kotlin/android/Manifest.permission#MANAGE_EXTERNAL_STORAGE), [Settings intent reference](https://developer.android.com/reference/kotlin/android/provider/Settings#ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION).

---

## 4. Background Processing Limitations

### WorkManager

The recommended background-work API. `Constraints` can gate work on network type (UNMETERED), charging, device idle, battery-not-low, storage-not-low, and content-URI changes. Key limitations:

- Work is **deferred until constraints are met**; if a constraint breaks mid-run, the worker is stopped and retried later.
- `PeriodicWorkRequest` has a **minimum repeat interval of 15 minutes** and is explicitly **inexact** "due to battery optimizations and doze mode."
- WorkManager is **not** for continuous or real-time execution.
- Long-running workers (WorkManager 2.7+, API 30+) wrap work in a foreground service via `setForeground()`/`setForegroundAsync()` with a `ForegroundInfo` notification. On API 34+ a foreground-service **type** must be specified at runtime, and the system checks prerequisites per type.

Sources: [Work constraints](https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started/define-work), [PeriodicWorkRequest](https://developer.android.com/reference/kotlin/androidx/work/PeriodicWorkRequest), [Long-running worker foreground-service type](https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/long-running).

### Foreground service requirements (long-running indexing)

- A foreground service **must** post an ongoing notification (user-visible).
- API 34+: declare service type in manifest (`dataTransfer`, `location`, `mediaPlayback`, `camera`, `microphone`, `phoneCall`, etc.) and request the matching `FOREGROUND_SERVICE_*` permission plus `FOREGROUND_SERVICE`; missing permission throws `SecurityException`.
- API 31+: starting foreground services from the background is heavily restricted (exemptions only for specific use cases).
- Even so, OEM battery optimization can still kill or restrict foreground services unless the user whitelists the app (see section 5).

Sources: [Foreground service changes API 34](https://developer.android.com/develop/background-work/services/fgs/changes), [Foreground service types](https://developer.android.com/develop/background-work/services/fgs/service-types).

### Doze and App Standby

Active from API 23 regardless of targetSdk:

- **Doze** (screen off, device unplugged, stationary): defers jobs, alarms, and network access to maintenance windows.
- **App Standby**: apps unused for a while lose network and job/alarm privileges outside daily maintenance windows.

Resource-limit matrix (from docs):

| Device state | Jobs | Alarms | Network | FCM |
|---|---|---|---|---|
| Charging | No limits (except restricted bucket) | No limits | No restrictions | No restrictions |
| Screen on | Limits per standby bucket | Limits per bucket/process state | Per bucket/process state | No restrictions |
| Screen off + Doze | Deferred to maintenance window | Regular alarms deferred; while-idle alarms limited to 7/hour | Restricted during doze | High priority: none; Normal: deferred |

`isBackgroundRestricted()` (ActivityManager): if the user has manually restricted the app's battery usage, **jobs and alarms will not execute and foreground services cannot be started unless an activity is in the foreground** — restrictions persist even while charging.

Sources: [Power management restrictions](https://developer.android.com/topic/performance/power/power-details), [Optimize for Doze and App Standby](https://developer.android.com/training/monitoring-device-state/doze-standby).

### JobScheduler

`JobInfo.Builder` supports constraints: required network type, requires charging, requires device idle, trigger content URIs, periodic/backoff policies. Jobs run in a `JobService.onStartJob()` (service must return promptly; work should move to a separate thread). Subject to the same Doze/standby restrictions as WorkManager (WorkManager uses JobScheduler on API 23+). Source: [Background optimization / JobScheduler](https://developer.android.com/topic/performance/background-optimization).

### Exact alarms

API 31+: apps targeting Android 12+ need `SCHEDULE_EXACT_ALARM` (special access, user-revokable; request via `ACTION_REQUEST_SCHEDULE_EXACT_ALARM`) for `setExact*`/`setAlarmClock`. Apps targeting API 33+ may instead use `USE_EXACT_ALARM` for core user-facing functionality. Exact alarms are **not** a reliable background-indexing trigger.

Sources: [Scheduling alarms](https://developer.android.com/develop/background-work/services/alarms), [AlarmManager.canScheduleExactAlarms](https://developer.android.com/reference/kotlin/android/app/AlarmManager#canScheduleExactAlarms).

### Can an Android app index files in the background continuously?

**No — not continuously and not reliably.** WorkManager is deferred/inexact and bounded by Doze/standby buckets; alarms are restricted; `isBackgroundRestricted()` kills jobs/alarms/foreground services; OEMs aggressively kill background processes (section 5). The practical pattern is:

- Short indexing batches while the app is in use (work continues briefly via foreground service if needed).
- Large batches via foreground service with persistent notification and explicit user initiation, accepting that some devices will still kill it.
- Opportunistic sync when the app is opened or when WorkManager constraints happen to be met.

---

## 5. Battery and Memory Optimization

### App standby buckets (API 28)

`UsageStatsManager.getAppStandbyBucket()` assigns each app to: `ACTIVE`, `WORKING_SET`, `FREQUENT`, `RARE`, `RESTRICTED` (plus special `NEVER` for never-run apps). Restrictions increase from ACTIVE to RESTRICTED:

- Buckets &gt; `FREQUENT` may have **network restricted** in background.
- `RARE` apps get a daily window at minimum to run jobs/network.
- `RESTRICTED` (heavy resource use or undesirable behavior) is most constrained.
- Every **manufacturer can set its own bucketing criteria**; ML-based prediction may move apps unpredictably.
- Doze-exemption-list apps are exempt from bucket-based restrictions.

Sources: [App Standby Buckets](https://developer.android.com/topic/performance/appstandby), [getAppStandbyBucket](https://developer.android.com/reference/kotlin/android/app/usage/UsageStatsManager#getAppStandbyBucket()).

### OEM background restrictions

The "Don't kill my app!" vendor comparison scores manufacturers (more poop emoji = more aggressive background killing):

- Most aggressive: Huawei, Xiaomi, OnePlus, Samsung
- Next: Meizu, Asus, Ulefone/RugOne, Oppo
- Mid: Wiko, Vivo, Tecno, realme, Motorola, Lenovo, Blackview
- Lighter: Sony, Unihertz
- Cleanest: Google/AOSP, Nokia/HMD, HTC

Users must perform vendor-specific whitelisting steps; background processing is unreliable by default because vendors "prefer battery life over proper functionality of your apps" — apps often die unless manually exempted. Even whitelisting is per-device and per-user; BARGEHAM cannot depend on it.

Source: [dontkillmyapp.com](https://dontkillmyapp.com/).

### Memory limits for large document processing

- `ActivityManager.getMemoryClass()`: per-app normal heap in MB; baseline 16 MB, commonly 24–96 MB+ depending on device.
- `getLargeMemoryClass()` (API 11+): heap with `android:largeHeap="true"`; may equal memory class on constrained devices or be much larger on RAM-rich devices; docs say most apps should not need it.
- Bitmaps and decoded PDF pages count toward the JVM heap. Large documents (hundreds of pages, high-resolution scans) can exceed the heap.
- **Strategy:** stream/render page-by-page (PdfRenderer opens one page at a time), downscale images for OCR, process documents in chunks, prefer native (C/C++) memory for decoding via NDK where the heap is the bottleneck.

Sources: [getMemoryClass](https://developer.android.com/reference/kotlin/android/app/ActivityManager#getMemoryClass()), [getLargeMemoryClass](https://developer.android.com/reference/kotlin/android/app/ActivityManager#getLargeMemoryClass()).

---

## 6. Synchronization with Windows

### Approaches

1. **Cloud relay (recommended architecture):** BARGEHAM Windows app &lt;-&gt; BARGEHAM cloud service &lt;-&gt; BARGEHAM Android app. Works around Android's inability to reach arbitrary Windows shares, NAT/firewall issues, and background-kill problems. Android uploads/downloads when the app runs or via WorkManager with UNMETERED-network constraints.
2. **Direct LAN sync (SMB/WebDAV/WebSocket):** Windows exposes a local server; Android discovers it on the same Wi-Fi. Fails when networks differ, when Android is backgrounded (Wi-Fi may be suspended in Doze), and with AP isolation. Requires foreground-service-like behavior for transfers — fragile on Android.
3. **Syncthing-style P2P:** The official `syncthing-android` wrapper app is **discontinued** (last release December 2024; Google Play publishing difficulties + no maintenance). Community forks exist (e.g., BasicSync, Syncbox-android), and one community project embeds Syncthing in Android **as a foreground service** — confirming that continuous P2P sync on Android requires foreground-service workarounds and is itself unmaintained/fringe. Not a dependable foundation for BARGEHAM.
4. **Custom sync over HTTP/gRPC to a BARGEHAM sync server** (self-hosted or SaaS): most controllable; handles offline queues, delta sync, conflict resolution.

Sources: [syncthing-android (discontinued)](https://github.com/syncthing/syncthing-android), [syncthing-android foreground-service embed (community)](https://github.com/spencer-tsai/syncthing-android).

### Offline-first sync strategy

- Local Room/SQLite database on Android stores documents, extracted text, OCR results, embeddings, and a sync queue (create/update/delete with timestamps and device IDs).
- Sync only when network available (WorkManager `UNMETERED` constraint or on app launch), uploading/downloads in chunks; resume after interruptions.
- Last-write-wins or vector-clock conflict resolution; user-visible conflict UI for conflicting document edits.
- Background sync windows are opportunistic — do not promise real-time sync.

---

## 7. OCR and Image Understanding on Android

### ML Kit Text Recognition (Google) — recommended

- On-device text recognition for images/video; bundled or unbundled (Play Services) installation.
- **Bundled** (`com.google.mlkit:text-recognition`): ~4 MB size increase per script per architecture; model available immediately; works fully offline.
- **Unbundled** (`com.google.android.gms:play-services-mlkit-text-recognition`): ~260 KB per script architecture; model downloaded dynamically via Google Play Services; first use may wait for download.
- Scripts: Latin, Chinese, Devanagari, Japanese, Korean (v2). Real-time on most devices for Latin; slower for other scripts.
- Minimum SDK: API 23.

### Tesseract on Android (tess-two) — NOT recommended

- `tess-two` (rmtheis/tess-two) is **no longer maintained** ("This project won't be receiving further updates"; try forks such as Tesseract4Android). Bundles Tesseract 3.05 / Leptonica 1.74.1 — very outdated OCR engine. Java API over native libs; traineddata files must ship with the app.

### PaddleOCR mobile

- PaddleOCR (PaddlePaddle) supports Android mobile/edge deployment via Paddle Lite (e.g., PP-OCRv4-mobile + Paddle Lite v2.14 in community demos). Purely community/demo Android integrations; no official Google-backed Android SDK. Evaluation needed for model size, accuracy, and NNAPI/CPU performance.

### On-device vs cloud OCR tradeoffs

| | On-device (ML Kit bundled, Tesseract, PaddleOCR) | Cloud OCR |
|---|---|---|
| Offline | Yes | No (needs network) |
| Latency | Local; depends on device CPU/NPU | Network round-trip |
| Privacy | Documents never leave device | Documents sent to provider |
| Cost | Free (no per-page API fees) | Per-page/per-call pricing |
| Accuracy | Good for clean scans; script-limited | Generally higher; language-rich |
| App size | +260 KB to several MB | None |

**Recommendation:** ML Kit bundled (offline capable, API 23+, maintained by Google), with optional cloud fallback for difficult documents where network is available.

Sources: [ML Kit text recognition Android v2](https://developers.google.com/ml-kit/vision/text-recognition/v2/android), [tess-two README](https://github.com/rmtheis/tess-two), [PaddleOCR Android demo repos](https://github.com/search?q=PaddleOCR+Android+mobile+OCR&amp;type=repositories).

---

## 8. Local Document Analysis on Android

### PDF parsing/rendering

| Library | Notes |
|---|---|
| **PdfRenderer** (Android framework, API 21+) | Renders PDF pages one at a time to `Bitmap`; thread-safe but only one page open at a time; `render()` is long-running → background thread. **No text extraction** (rendering only). |
| **PdfiumAndroid / android-pdf-viewer** (barteksc) | Community libraries wrapping Pdfium: rendering + text search/selection. Large native binaries (~15–25 MB APK impact); community-maintained. |
| **Pdfium (NDK)** | Google's Pdfium consumed via NDK; most control, largest engineering effort. |

Source: [PdfRenderer reference](https://developer.android.com/reference/kotlin/android/graphics/pdf/PdfRenderer).

### Local embedding models

| Option | Android viability |
|---|---|
| **LiteRT / TensorFlow Lite** | On-device ML for mobile/edge; Java/Kotlin `Interpreter` API; models converted via `TFLiteConverter`. GPU/NNAPI delegates available. Mature, officially supported by Google. |
| **ONNX Runtime Mobile** | `onnxruntime-android` AAR; `android_min_sdk_version = 24`; execution providers: NNAPI (Android NPU), XNNPACK (CPU), WebGPU (Dawn/Vulkan), QNN (Qualcomm NPU, arm64-v8a only). Java API: `OrtEnvironment.createSession`, `OnnxTensor`, `session.run`. |
| **LanceDB** | SDKs: Python, TypeScript, Rust only (**no official Android/Kotlin SDK**; LanceDB SwiftKit is iOS/macOS only). Not directly usable on Android today without bindings work. |
| **sqlite-vec** | Pure C vector-search SQLite extension ("runs anywhere SQLite runs"); pre-v1 (breaking changes expected); float/int8/binary vectors in `vec0` virtual tables; KNN via `match ... order by distance`. Android SQLite is available via NDK/bundled sqlite3, so a native android integration is feasible but requires packaging the `.so` extension. |

Source: [TensorFlow Lite](https://www.tensorflow.org/lite/) via [TensorFlow docs](https://github.com/tensorflow/docs), [ONNX Runtime android build settings](https://github.com/microsoft/onnxruntime/blob/main/tools/ci_build/github/android/default_full_aar_build_settings.json), [OrtSession Java API](https://github.com/microsoft/onnxruntime/blob/main/java/src/main/java/ai/onnxruntime/OrtSession.java), [sqlite-vec](https://github.com/asg017/sqlite-vec), [LanceDB SDKs](https://github.com/lancedb/lancedb/blob/main/docs/web/basics/sdk.mdx).

### Memory implication

Decode/render at the resolution actually needed; downscale images before OCR; keep embeddings small (e.g., 384–768 dims); process documents page-by-page rather than loading whole PDFs into the heap (section 5).

---

## 9. Offline Functionality

| Fully offline on Android | Requires cloud / network |
|---|---|
| User-picked folder/file access via persisted SAF URIs | Initial folder picking (needs user interaction, not network) |
| MediaStore reads of own media + `READ_MEDIA_*` media | Accessing other apps' non-media files without SAF/MANAGE_EXTERNAL_STORAGE |
| PDF rendering page-by-page (PdfRenderer/Pdfium) | Cloud-only OCR engines |
| ML Kit bundled OCR (offline) | ML Kit unbundled first-use model download |
| Tesseract/PaddleOCR local models | Model downloads for unbundled/online OCR |
| Local SQLite/Room index + sqlite-vec vector search | Cross-device sync, multi-user collaboration |
| Local embedding inference (LiteRT/ONNX Runtime) | Cloud embeddings/LLM-based understanding |
| On-device search, filtering, full-text search | Sync with Windows desktop / other devices |
| Local document edits, annotations | Real-time collaboration |

**Bottom line:** capture, OCR, index, and search can work fully offline on Android if BARGEHAM uses bundled on-device models and local storage. Sync with Windows and any cloud AI features require network.

---

## 10. What is Practically Achievable vs What Requires Workarounds

| Capability | Achievable on Android? | Notes / workaround |
|---|---|---|
| Scan entire device for documents | **No** | Scoped storage forbids arbitrary paths (section 3). Workaround: user-picked folders (SAF, persisted URIs) + MediaStore media; `MANAGE_EXTERNAL_STORAGE` only for file-manager-like apps with Play approval. |
| Remember folder access across reboots | **Yes** | `takePersistableUriPermission()` persists grants across reboots; lost if folder moved/deleted → re-pick. |
| Read other apps' images/PDFs in Downloads | **Partially** | Images/video/audio via `READ_MEDIA_*` (API 33+); PDFs/non-media in Downloads are **not** in MediaStore → SAF or All Files Access. |
| Continuous background indexing | **No** | Doze/standby buckets, `isBackgroundRestricted()`, WorkManager inexactness, OEM kills. Workaround: foreground service for user-initiated batches + opportunistic WorkManager sync. |
| Foreground service for long-running indexing | **Yes (API 34+ caveats)** | Ongoing notification + service type + `FOREGROUND_SERVICE_*` permissions; still killable by OEMs unless user whitelists. |
| Reliable background sync on battery-restricted devices | **No** | Sync on app launch / when constraints met; cloud relay so Windows&lt;-&gt;Android sync doesn't require simultaneous online presence. |
| On-device OCR offline | **Yes** | ML Kit bundled (~4 MB/script/arch, API 23+); Tesseract unmaintained; PaddleOCR community only. |
| PDF text extraction + rendering | **Partial** | PdfRenderer (API 21+) renders pages only, no text extraction; Pdfium-based community libs add text but increase APK size. |
| Local vector search of document embeddings | **Feasible, immature** | sqlite-vec (pure C, pre-v1) via NDK; LanceDB has no Android SDK; requires custom integration and memory discipline. |
| Sync with Windows Desktop | **Via cloud relay** | Direct P2P (Syncthing) official Android app discontinued; LAN sync fragile under Doze. |

---

## 11. Recommended Android Technology Stack

| Layer | Technology | License | Notes |
|-------|-----------|---------|-------|
| UI Framework | **Kotlin + Jetpack Compose** | Apache-2.0 | Modern Android UI toolkit; Material Design 3 |
| Local Database | **Room / SQLite** | Apache-2.0 / Public Domain | Documents, extracted text, sync queue |
| Vector Search | **sqlite-vec** (via NDK) | MIT | Pre-v1; custom integration required |
| File Access | **SAF + MediaStore** | Android framework | User-picked folders; persisted URI permissions |
| OCR | **ML Kit bundled** | Google ToS | Offline, API 23+, ~4 MB/script/arch |
| PDF Rendering | **PdfRenderer** (API 21+) | Android framework | Page-by-page; no text extraction |
| PDF Text Extraction | **PdfiumAndroid** (community) | Apache-2.0 | Community-maintained; ~15-25 MB APK impact |
| Embeddings | **ONNX Runtime Mobile** | MIT | NNAPI/CPU; Android AAR |
| Background Work | **WorkManager** | Apache-2.0 | Inexact/deferred; best-effort only |
| Long-running Tasks | **Foreground Service** | Android framework | API 34+ service type + notification |
| Network | **OkHttp / Retrofit** | Apache-2.0 | Sync with BARGEHAM cloud relay |
| Dependency Injection | **Hilt** | Apache-2.0 | Google-recommended DI for Android |
| Packaging | **APK / AAB** | N/A | AAB for Google Play Store |

---

## 12. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| User denies folder access | High | Medium | Clear onboarding; explain why access needed; re-prompt gracefully |
| Folder moved/deleted (lost URI grant) | Medium | Medium | Detect failure; re-prompt user to re-select folder |
| Background indexing killed by OEM | High | High | Foreground service + notification; advise user to whitelist on Samsung/Xiaomi/OnePlus/Huawei |
| Memory OOM on large PDFs | Medium | High | Page-by-page rendering; downscale images; native memory via NDK |
| Google Play rejection (MANAGE_EXTERNAL_STORAGE) | Medium | High | Avoid declaring it; rely on SAF + MediaStore only |
| No reliable continuous sync | Medium | Medium | Cloud relay; sync on app launch; offline-first queue |
| Persian OCR accuracy | Medium | Medium | Test with real Persian documents; allow user correction |

---

## Sources (official)

1. Android developer training — Data and storage overview: https://developer.android.com/training/data-storage
2. Storage Access Framework / documents and files: https://developer.android.com/training/data-storage/shared/documents-files
3. ContentResolver.takePersistableUriPermission: https://developer.android.com/reference/kotlin/android/content/ContentResolver#takePersistableUriPermission(android.net.Uri,kotlin.Int)
4. Intent.ACTION_OPEN_DOCUMENT: https://developer.android.com/reference/kotlin/android/content/Intent#ACTION_OPEN_DOCUMENT:kotlin.String
5. MediaStore media access and permissions: https://developer.android.com/training/data-storage/shared/media
6. Manage all files (MANAGE_EXTERNAL_STORAGE) + Google Play notice: https://developer.android.com/training/data-storage/manage-all-files
7. Manifest.permission.MANAGE_EXTERNAL_STORAGE: https://developer.android.com/reference/kotlin/android/Manifest.permission#MANAGE_EXTERNAL_STORAGE
8. Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION: https://developer.android.com/reference/kotlin/android/provider/Settings#ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION
9. Environment.isExternalStorageManager: https://developer.android.com/reference/kotlin/android/os/Environment#isExternalStorageManager()
10. Photo Picker (PickVisualMedia): https://developer.android.com/training/data-storage/shared/photo-picker
11. Android 15 features (selected photos access): https://developer.android.com/about/versions/15/features
12. Power management restrictions (Doze/standby matrix): https://developer.android.com/topic/performance/power/power-details
13. Optimize for Doze and App Standby: https://developer.android.com/training/monitoring-device-state/doze-standby
14. App Standby Buckets: https://developer.android.com/topic/performance/appstandby
15. ActivityManager.getMemoryClass / getLargeMemoryClass: https://developer.android.com/reference/kotlin/android/app/ActivityManager
16. UsageStatsManager.getAppStandbyBucket: https://developer.android.com/reference/kotlin/android/app/usage/UsageStatsManager#getAppStandbyBucket()
17. ActivityManager.isBackgroundRestricted: https://developer.android.com/reference/android/app/ActivityManager#isBackgroundRestricted()
18. Foreground service changes (API 34): https://developer.android.com/develop/background-work/services/fgs/changes
19. Foreground service types: https://developer.android.com/develop/background-work/services/fgs/service-types
20. Long-running workers and foreground service types: https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/long-running
21. Work constraints (WorkManager): https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started/define-work
22. PeriodicWorkRequest reference: https://developer.android.com/reference/kotlin/androidx/work/PeriodicWorkRequest
23. Scheduling alarms (SCHEDULE_EXACT_ALARM): https://developer.android.com/develop/background-work/services/alarms
24. PdfRenderer: https://developer.android.com/reference/kotlin/android/graphics/pdf/PdfRenderer
25. ML Kit text recognition on Android (v2): https://developers.google.com/ml-kit/vision/text-recognition/v2/android
26. tess-two (Tesseract Android) — no longer maintained: https://github.com/rmtheis/tess-two
27. ONNX Runtime (Android AAR, NNAPI/XNNPACK/WebGPU/QNN): https://github.com/microsoft/onnxruntime
28. sqlite-vec (local vector search, pre-v1): https://github.com/asg017/sqlite-vec
29. LanceDB SDKs (no Android SDK): https://github.com/lancedb/lancedb/blob/main/docs/web/basics/sdk.mdx
30. Don't kill my app (OEM background-kill comparison): https://dontkillmyapp.com/
31. syncthing-android (discontinued Dec 2024): https://github.com/syncthing/syncthing-android
32. syncthing-android foreground-service embed (community): https://github.com/spencer-tsai/syncthing-android
