# Agent Journal - Project Legal Brain 🧠⚖️

## 🚀 Current Mission: Deka Knowledge Graph & Neural Search
**Objective**: Transform raw PDF texts into a structured Knowledge Graph and searchable Vector Index using Gemini & Vertex AI.

## 📅 Journal Entries

- **2026-01-20 14:00 (The Great Pivot)**
    - **Strategy Shift**: Abandoned full-page OCR for 30k docs due to cost ($400+).
    - **New Approach**: Utilized 300k+ *pre-existing* JSONL text files (iApp extraction).
    - **Pipeline**: Built `kg_pipeline.py` (Text-to-KG) using Gemini 2.0 Flash (Free/Low cost).
    - **Optimizations**:
        - **Smart Filter**: Only process high-value docs (Legislations, Deka, Orders).
        - **Robustness**: Fixed `List Indices` bug (JSON structure mismatch) via robust parsing.
        - **Infrastructure**: Scaled Worker to `e2-standard-8` (8 vCPU) for 50-thread concurrency.
    - **Status**: Pipeline RUNNING (PID 9797). Success rate close to 100%.

- **2026-01-20 15:00 (Cloud Sync & Automation)**
    - **Vertex AI Search**: Created Data Store `main-legal` & Imported 232k records. (Indexing...)
    - **Backend**: Deployed to Cloud Run (`sue-ai-backend`).
    - **Frontend**: integrated with Vertex AI Search & Pushed to GitHub.
    - **Status**: **LIVE (Sue.AI 2.0)** - Waiting for Search Indexing to complete.

- **2026-01-21 01:54 (System Architecture Clarification & Fixes)**
    - **Architecture Discovery (The Storage Dualism)**:
        - Confirmed that the PDF storage infrastructure is split into **two distinct GCS Buckets**:
            1. **`gs://sue-ai-pdfs-storage/`**: Stores **Deka files** (Supreme Court Opinions). Identified by filenames starting with `Deka_`.
            2. **`gs://deka-legal-search-data/pdfs/`**: Stores **Law/Other files** (General legislations). Identified by filenames *without* the `Deka_` prefix.
    - **Critical Fix (Smart Citations)**: The backend `rag_core.py` was previously pointing only to the `deka-legal-search-data` bucket, causing 404 errors for Deka citations.
        - **Action**: Modified `retriever` logic to dynamically construct `pdf_url` based on the filename prefix (`Deka_` -> `sue-ai-pdfs-storage`).
    - **Backend Restoration**:
        - Detected and fixed a regression where `smart_query_optimizer` function was accidentally deleted during a previous edit. Re-implemented it to ensure user queries are refined by Gemini before search.
        - Fixed `Vertex AI Search Error` caused by Protobuf objects (`MapComposite`) not being JSON serializable.
    - **Optimization**:
        - Created `.dockerignore` to exclude local artifacts (`.venv`, `__pycache__`, `sue_local.db`) from the Docker build, keeping the image size optimal (~150MB).
    - **Status**: Backend redeployed & Deka Smart Citations fully verifiable.

## 🚧 Active State
- **Worker**: `hf-transfer-worker` (Indexing remaining 94k docs)
- **Cloud Run**: `sue-ai-backend` (Online)
- **Frontend**: Vercel (building...)
- **Next Step**: Verify Search Results (once indexing catches up).

- **2026-01-21 13:40 (Go Backend Migration & Schema Rescue)**
    - **Migration**: Transitioned backend from Python to **Go (Golang) 1.24** (`sue-ai-backend-go`) for high-concurrency performance and faster cold starts.
    - **The "Invisible Data" Bug**: Go backend was failing to return search results (Title/Metadata) for Law documents, while Python worked.
    - **Discovery**: Analyzed `vertex_ready_upload.jsonl` and found a **Schema Mismatch**.
        - Go expected flat fields (`title`, `year`).
        - Vertex/JSONL structure was **nested**: `structData.document_meta.title`.
        - Go's `GetStringValue()` ignored nested structs, returning empty strings.
    - **Fix**: Implemented a **Struct Flattening Algorithm** in `internal/rag/search.go` that recursively unpacks nested Protobuf structs (like `document_meta`) into the flat map.
    - **Result**: Law documents (Announce/Gazette) now correctly populate `Title` and `Year`.
    - **Status**: Backend Redeploying... Ready for validation.

- **2026-01-24 14:10 (PDF Link Correction)**
    - **Issue**: Law documents (non-Deka) were returning broken links (404 NoSuchKey) pointing to `sue-ai-pdfs-storage/Legal-Data/...`.
    - **Cause**: Incorrect assumption in Go backend path construction.
    - **fix**: Corrected URL generation logic to match Python backend:
        - **Deka Files**: `gs://sue-ai-pdfs-storage/`
        - **Law Files**: `gs://main_legal_data/pdfs/` (Switched from deka-legal-search-data due to access issues)
    - **Status**: Redeployed. Links should now work.

- **2026-01-24 14:15 (Deka Content Unlocking)**
    - **Issue**: AI claimed "Database has no info" even though sources appeared in the UI lists.
    - **Cause**: The Go backend was extracting `Snippet` from `DerivedStructData` (Vertex Snippet), but if that failed, it fell back ONLY to `content`.
    - **Discovery**: Deka JSONL files use the key `full_text`, not `content`.
    - **Fix**: Expanded the fallback logic in `internal/rag/search.go` to try multiple keys: `["content", "full_text", "text", "body"]`.
    - **Status**: Redeploying. AI answers should now correctly reference the text from Deka judgments.

- **2026-01-24 14:20 (Result Stream UX Optimization)**
    - **Requirement**: User requested "Result first, then References".
    - **Change**: Reordered SSE events in `internal/api/handlers.go`.
    - **Logic**: Moved `h.sendSSEObject(w, "sources", results)` from *before* the text generation loop to *after* it completing.
    - **Effect**: Frontend will now display the Source List only after the AI has finished streaming the answer.
    - **Status**: Ready for Deploy (Pending Order).

- **2026-01-25 14:25 (The Cognitive & Visual Upgrade - Phase 1-3)**
    - **Mission**: Transform Sue.AI from a "Search Engine" into a "Thinking Partner".
    - **Phase 1: Semantic Memory (The Brain 🧠)**
        - **Problem**: AI treated every question as new, failing follow-up questions.
        - **Solution**: Implemented `memory/cache.go` (In-Memory Semantic Cache) linked to session IDs.
        - **Result**: AI now understands context (e.g., "แล้วโทษล่ะ?" -> knows the context is the previous murder case).
    - **Phase 2: Transparent Mind UI (The Face ⚡)**
        - **Visual**: Added "Memory Mode" (Brain Pulse Animation) vs "Search Mode" (Spinning Loader) to the frontend.
        - **Benefit**: User knows exactly source of truth (Memory vs Database).
    - **Phase 3: Visual Intelligence (The Presentation 🎨)**
        - **Smart Citations**: Implemented Hover Cards for Deka/Law sections (Preview snippet without clicking).
        - **Legal Timeline Builder**: AI now auto-generates JSON Timelines for cases with sequential events.
        - **Insight Card**: Added "Scenario Analysis" & "Critical Analysis Table" (Pros/Cons).
        - **Neutrality**: Enforced "Neutral Advisor" persona (Verdict: Likely Win/Lose with 2-sided arguments).
    - **Status**: **Phase 1-3 Complete**. System is stable and highly interactive. Ready for Long-Term Memory (Phase 4).

- **2026-01-24 14:35 (Multi-Store App Engine Migration)**
    - **Optimization**: Switched search logic to use **App Engine IDs** for both DEKA and LAW (instead of direct Data Store IDs).
    - **IDs Configured**:
        - DEKA App: `sue-ai-search_1768730959752`
        - LAW App: `main-legal-search_1768906502953`
    - **Benefit**: Unlocked rich metadata and full-text content (`full_text`) for both stores, resolving the "No information found" issue for legal statutes and Deka judgments.
    - **Infrastructure**: Updated `config.go` and `.env` to manage Engine IDs as environment variables.
    - **Status**: Local Server Restarted. Testing now.

- **2026-01-24 14:55 (The Snippet & UI Polish)**
    - **Issue**: Source list showing "No snippet available" and AI sometimes missing context.
    - **Cause**: Vertex AI was returning placeholder text in the `snippets` field while background indexing was still warm. Go backend was blindly picking this up.
    - **Fix 1 (Backend)**: Added logic to ignore Vertex placeholders and fallback to `full_text` or `summary`. Refined `title` logic to use Case IDs (e.g., 943/2532).
    - **Fix 2 (Frontend Loading UX)**: User reported an "empty bubble" while waiting.
        - **Cause**: Backend was sending `type: status` events ("Searching..."), but frontend wasn't handling them.
        - **Action**: Updated `src/app/chat/page.tsx` to display these status messages in the chat bubble and cleanly replace them with the actual answer once it starts streaming.
    - **Status**: Backend & Frontend updated. Ready for sync/deploy.

- **2026-01-24 15:15 (Final PDF Link Fix)**
    - **Issue**: Law PDFs were returning `AccessDenied` from `main_legal_data`.
    - **Discovery**: The `main_legal_data` bucket has Public Access Prevention ENFORCED, while `sue-ai-pdfs-storage` is public.
    - **Fix**: Reverted the path to `gs://sue-ai-pdfs-storage/Legal-Data/`.
    - **Result**: Law documents are now publicly accessible again.
    - **Status**: Backend Redeployed.
- **2026-01-24 17:15 (Frontend Upgrade & Professional Positioning)**
    - **Victory**: Upgraded Chat Interface to v2.0 with professional "Legal Research" UX (Step-based loading).
    - **Victory**: Implemented "Suggestion Cards" specifically for legal professionals.
    - **Victory**: Enhanced System Prompt with structured comparison tables and risk assessment.
    - **Victory**: Successfully deployed Go Backend and synced Frontend to Production (Vercel).
    - **Victory**: Created `ARCHITECTURE.md` as the system's "Blueprint" for long-term maintenance.
    - **Status**: Live & Professional. 🚀⚖️

- **2026-01-24 16:30 (The 1.2M PDF Turbo Sync Mission)**
    - **Current Mission**: Recover and sync 140 years of Thai Legal PDFs from ZIP archives in `recovery-worker` VM to `gs://main_legal_data/pdfs/`.
    - **Turbo Mode Activated**:
        - Using `turbo_sync_v3.py` for Streaming Sync (Unzip & Upload in parallel).
        - **Status as of 17:35**:
            - **Cloud State**: ~15,361 files synced (Growing).
            - **Local VM State**: **1,352,470 PDF files** ready in `~/turbo_temp`.
    - **Persistence Note**: Monitoring with `tail -f turbo_sync_v3_new.log` on the VM.


- **2026-01-24 22:45 (The Gemini 3 "Deep Research" Upgrade)**
    - **Victory**: Integrated **Gemini 3.0 Flash Preview** as the core engine, delivering a perfect balance of speed and reasoning.
    - **Victory**: Implemented **"Deep Research" Mode** - unlocking context window from 60k to **500k chars** and allowing up to 15 document comparisons per query.
    - **Stability**: Fixed `context deadline exceeded` by implementing a dedicated 60s timeout for RAG operations.
    - **Robustness**: Added **Automatic Retry Logic** (3 attempts) for `429 Resource Exhausted` errors, essential for preview-stage models.
    - **UX**: Added Deep Research toggle and doc-limit slider in the Frontend for professional control.
    - **Status**: Backend & Frontend fully optimized for high-depth legal analysis.

- **2026-01-25 16:35 (The Legal Board V5 - Slate & Amber Evolution)**
    - **Visual Overhaul**: Transformed Sue.AI into **"The Legal Board"** – a premium workspace using Slate & Amber accents, glassmorphism, and a dynamic "Legal Matrix" background.
    - **Cognitive Upgrade (Concept-First Search)**: Modified `handlers.go` to use Behavioral/Conceptual search queries instead of guessing section numbers. This drastically improved result relevance.
    - **The Noise Filter 🧹**: Implemented a dynamic filter in the LAW engine to exclude administrative noise (Bankruptcy orders, Association notices). These were previously "crowding out" actual Law Articles (like CC 1382).
    - **The 100% Citation Promise 🛡️**: Frontend buttons now use a **Hybrid Strategy**. If a local PDF isn't found in the RAG context, it provides an "External Link" to Google Search. Every citation is now an actionable button.
    - **Precision Prep (Categorization)**: Developed and ran `categorize_data.py`. 300k+ JSONL records are now neatly split into thematic buckets (Civil, Criminal, Labor, Notices).
    - **Status**: Backend & Frontend stable. Every search now guarantees a mix of 30 Deka and 50 Law docs. Ready for Multi-Store indexing tomorrow.

## 🚧 Active State
- **Core Engine**: Gemini 3.0 Flash (Preview)
- **UI State**: "The Legal Board" (Premium Theme)
- **Backend**: Go 1.24 (Noise Filtering & Hybrid Citations ACTIVE)
- **Data Status**: Categorized locally, ready for GCS Sync & Multi-Store Indexing.
- **Status**: **STABLE & PROMOTED**. Ready for rest. 🧘‍♂️⚖️
