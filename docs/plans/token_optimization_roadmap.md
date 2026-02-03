# Token & Cost Optimization Roadmap: "The DeepSeek Way"

**Target:** Reduce cost per request from ~$0.12 (4.30 THB) to < $0.008 (0.28 THB).
**Current Status:** Full Load (Top-50 Docs, 200k+ tokens).

---

## 🗺️ Phase 1: "Immediate Relief" (Plan A)
**Goal:** 15x Cost Reduction with minimal code changes.
**Risk:** Low

### 1.1 Config Hard Cap
- **Action:** Modify `internal/rag/search.go`
- **Change:** Set `PageSize` (Top-K) to **10** (from default 50).
- **Impact:** Input token reduced by 80%.

### 1.2 Content Truncation
- **Action:** Modify `internal/api/handlers.go` (Loop processing RAG results)
- **Change:** 
    - Truncate document content to `2,000` characters max.
    - Remove redundant metadata tags from the prompt context string.
- **Impact:** Input token per doc reduced from ~5k to ~1k.

### 1.3 Prompt Cleanup
- **Action:** Refine System Prompt in `handlers.go`.
- **Change:** Remove lengthy few-shot examples and instruction reptition.
- **Impact:** System prompt reduced by ~50%.

---

## 🚀 Phase 2: "Surgical Precision" (Plan B)
**Goal:** 98% Cost Reduction (< 0.08 THB) & Smarter retrieval.
**Risk:** Medium (Requires testing for accuracy)

### 2.1 Dynamic Relevancy Filter
- **Action:** Create `RelevanceFilter` in `optimizer.go`.
- **Logic:**
    - Fetch Top-10 docs (Metadata Only).
    - Check relevance score of Top-1.
    - Filter out any docs with score < (Top1_Score * 0.8).
    - If only 1-2 docs remain, fetch only those.

### 2.2 Snippet-First Strategy
- **Action:** Use `ExtractiveSegments` from Vertex AI.
- **Logic:**
    - Send ONLY snippets (300 chars) to Gemini first.
    - Add instruction: "If snippets are insufficient, request FULL_DOC_ID".
    - Backend parses response: If `FULL_DOC_ID` requested -> Fetch full text & Retry.

### 2.3 History Compression
- **Action:** Implement background summarizer.
- **Logic:** Compress chat history older than 3 turns into a single summary line.

---

## 📊 Monitoring Plan
1. Enable `UsageMetadata` logging in `handlers.go` (Already implemented).
2. Monitor log file daily to track Token Usage vs Request Count.
3. Compare cost before/after applying Phase 1.
