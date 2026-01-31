# 🧠 Sue.AI Evolution Plan: "The Digital Colleague" Implementation
> **Approved by:** The Sue.AI Advisory Board (5 Agents)
> **Date:** 2026-01-25
> **Objective:** Upgrade Sue.AI from a "Search Engine" to a "Thinking Partner" with persistent memory and natural conversation flow.

---

## 🏛️ Board of Agents Consultation

### 1. 👨‍💻 Senior Developer & Architect
**Opinion:** "The current 'Skip Search' logic is too naive (Hardcoded Heuristic). It breaks easily. We need a deterministic **Intent Classification** layer."
**Advice:**
- **Refactor:** Move the search logic out of `handlers.go` into a dedicated `Orchestrator`.
- **New Component:** `Intent Analyzer` – A lightweight LLM call (Gemini Flash) to decide: *Does this query need new info, or can I answer from history?*
- **Caching:** Implement **Semantic Caching** context, not just keeping the last 10 messages.

### 2. ⚖️ Legal Tech Specialist
**Opinion:** "Speed is good, but Accuracy is non-negotiable. If the user asks a follow-up that requires *new* legal facts, we MUST NOT skip search."
**Advice:**
- **Safety Check:** The `Intent Analyzer` must be biased towards "Search" if there's any ambiguity about a law section or Supreme Court ID.
- **Context Window:** The "Memory" must strictly separate "Facts provided by User" vs "Laws retrieved by System" to prevent mixing them up.

### 3. 🎨 UX/UI Designer
**Opinion:** "The user needs to feel the difference between 'Recalling' and 'Researching'. Naturalness comes from transparency."
**Advice:**
- **Dynamic Status:** Change the UI loading state based on intent:
  - 🔍 *Search Mode:* "Searching Deka Database..."
  - 🧠 *Memory Mode:* "Reviewing previous context..." or "Connecting the dots..."
- **Visual Cues:** Add a subtle "Memory Active" indicator when answering from history.

### 4. ⚡ Frontend Expert (Vercel)
**Opinion:** "The current chat state is fragile. If the user refreshes, the 'feeling' of the conversation needs to persist instantly."
**Advice:**
- **Optimistic UI:** Show the user's message immediately while the `Intent Analyzer` runs in the background.
- **Hybrid State:** Sync conversation state with `localStorage` for immediate "Time-to-Interactive" upon revisiting.

### 5. 👁️ Web Design Auditor
**Opinion:** "Ensure the new 'Thinking' states are accessible and distinct."
**Advice:**
- **Contrast:** Ensure the "Memory Mode" badge has high contrast (maybe Purple/Indigo) vs "Search Mode" (Blue/Primary).

---

## 📝 Detailed Implementation Plan

### Phase 1: The "Intent Brain" (Backend) 🧠
**Goal:** Replace `if len < 30` with true AI intelligence.

1. **Create `internal/agent/orchestrator.go`**:
   - Define a `ClassifyIntent(history, current_query)` function.
   - Use **Gemini 2.0 Flash** with `response_schema` to return strict JSON:
     ```json
     { "action": "SEARCH" | "ANSWER", "reason": "..." }
     ```
   - **Cost:** Virtually zero (Flash is cheap/fast), but High Value.

2. **Integration in `ChatStream`**:
   - Step 1: User sends message.
   - Step 2: **Intent Check** (parallels with history fetch).
   - Step 3:
     - If `SEARCH`: Run `RAGService.Search` (Current Flow).
     - If `ANSWER`: Skip search, inject `History + Last Retrieved Docs` into context.

### Phase 2: The "Transparent Mind" (Frontend) 🎨
**Goal:** Visualize the AI's decision process.

1. **Update `api/chat` Response Protocol**:
   - Send an initial SSE event: `type: 'status', mode: 'memory' | 'search'`.
   
2. **Modify `page.tsx`**:
   - Update the "Loading Indicator" to accept `mode` prop.
   - **Animation:**
     - Search: Spinning Globe / Magnifying Glass.
     - Memory: Glowing Brain / Connecting Nodes.

### Phase 3: Long-Term Memory (vector Store) 📚
**Goal:** "Save cache somewhere" as requested.

1. **Session Caching**:
   - Currently, we rely on the `contextText` string being rebuilt.
   - **Upgrade:** Store the *last retrieved documents* in a temporary variable (Redis or In-Memory Map keyed by `conversation_id`).
   - When `Intent = ANSWER`, retrieve these docs immediately without hitting Vertex AI again.

---

## 🚀 Execution Steps (Immediate)

1. [ ] **Backend:** Create `ClassifyIntent` function using Gemini Flash.
2. [ ] **Backend:** Refactor `ChatStream` to use the classifier.
3. [ ] **Backend:** Implement "Last Search Context" caching (In-Memory for now).
4. [ ] **Frontend:** Update UI to show "Thinking Mode" vs "Searching Mode".

**Ready to start Phase 1?**
