package api

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"
	"unicode/utf8"

	"sue-ai-backend/internal/agent"
	"sue-ai-backend/internal/memory"
	"sue-ai-backend/internal/rag"

	"github.com/gin-gonic/gin"
	"github.com/google/generative-ai-go/genai"
	"google.golang.org/api/iterator"
)

type ChatRequest struct {
	Question      string                 `json:"question" binding:"required"`
	Filters       map[string]interface{} `json:"filters"`
	DeepSearch    bool                   `json:"deep_search"`
	DocumentLimit int                    `json:"doc_limit"`
	History       []map[string]string    `json:"history"`
}

type Handler struct {
	RAG *rag.RAGService
}

func NewHandler(ragService *rag.RAGService) *Handler {
	return &Handler{RAG: ragService}
}

// ChatStream handles the chat request with SSE streaming
func (h *Handler) ChatStream(c *gin.Context) {
	var req ChatRequest

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Set Headers for SSE
	c.Writer.Header().Set("Content-Type", "text/event-stream")
	c.Writer.Header().Set("Cache-Control", "no-cache")
	c.Writer.Header().Set("Connection", "keep-alive")
	c.Writer.Header().Set("Transfer-Encoding", "chunked")
	c.Writer.Header().Set("X-Accel-Buffering", "no") // Prevent Cloud Run/Nginx buffering

	c.Stream(func(w io.Writer) bool {
		// Create a separate context with a healthy timeout for the RAG operations
		// This prevents "context deadline exceeded" during auth token refresh
		ragCtx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
		defer cancel()

		// Initialize Intent Analyzer
		analyzer := agent.NewIntentAnalyzer(h.RAG.GenClient)

		// Classify user intent (SEARCH vs ANSWER)
		intent, clsErr := analyzer.Classify(ragCtx, req.History, req.Question)
		if clsErr != nil {
			log.Printf("⚠️ Intent Classification failed: %v. Defaulting to SEARCH.", clsErr)
			intent = agent.IntentResult{Action: "SEARCH", Reason: "Error"}
		}

		log.Printf("🧠 Agent Decision: %s (Reason: %s)", intent.Action, intent.Reason)

		skipSearch := intent.Action == "ANSWER"

		// 1. Optimize Queries (Only if searching)
		var results []rag.SearchResult
		var searchErr error

		if !skipSearch {
			// Send Initial Status
			h.sendStatus(w, "กำลังสืบค้นฐานข้อมูลกฎหมายและฎีกา...", "SEARCH")

			optimizedQueries := h.RAG.OptimizeQueries(ragCtx, req.Question)

			// 2. Search
			results, searchErr = h.RAG.Search(ragCtx, optimizedQueries, req.Filters)
			if searchErr != nil {
				log.Printf("❌ Search Error: %v", searchErr)
				// Don't fail completely, try to answer with what we know/history
				h.sendStatus(w, "ค้นหาขัดข้อง กำลังพยายามตอบจากความรู้ที่มี...", "ANSWER")
			} else {
				// SAVE Context to Memory 🧠
				if convID := getConversationID(req.History); convID != "" {
					memory.GetMemory().SaveContext(convID, results)
					log.Printf("💾 Saved %d docs to memory for session %s", len(results), convID)
				}
			}
		} else {
			h.sendStatus(w, "กำลังวิเคราะห์จากบทสนทนาก่อนหน้า...", "ANSWER")
			// RETRIEVE Context from Memory 🧠
			if convID := getConversationID(req.History); convID != "" {
				cachedResults := memory.GetMemory().GetContext(convID)
				if cachedResults != nil {
					results = cachedResults
					log.Printf("🧠 Memory Hit! Loaded %d docs from cache for session %s", len(results), convID)
				} else {
					log.Printf("🧠 Memory Miss for session %s", convID)
				}
			}
		}

		log.Printf("🔍 Handler received %d results from Search", len(results))

		h.sendStatus(w, "กำลังประมวลผลคำตอบ...", "ANSWER")

		// 3. Generate Answer (Streaming)
		contextText := ""

		// DEFAULT Context (Fast Mode) - DOUBLED
		maxContextPerDoc := 30000 // Was 15000
		displayLimit := 5

		// DEEP RESEARCH Mode: Unlock Context - DOUBLED
		if req.DeepSearch {
			maxContextPerDoc = 200000 // Was 100K
			log.Printf("🚀 DEEP RESEARCH MODE ACTIVATED")
		}

		// Document Limit Override
		if req.DocumentLimit > 0 {
			displayLimit = req.DocumentLimit
			if displayLimit > 15 { // Cap it for safety
				displayLimit = 15
			}
		}

		// Building Context: Prioritize LAW docs first!
		var contextDocs []rag.SearchResult
		for _, doc := range results {
			if doc.Source == "LAW" {
				contextDocs = append(contextDocs, doc)
			}
		}
		// Add DEKA docs after LAW until we reach the limit
		for _, doc := range results {
			if doc.Source != "LAW" {
				contextDocs = append(contextDocs, doc)
			}
		}

		maxDocsInContext := 30 // Increased from 5 to 30 for complete coverage

		for i, doc := range contextDocs {
			if i >= maxDocsInContext {
				break
			}
			// Use Snippet, but fallback to Content or Meta's full_text if empty
			textContent := doc.Snippet
			if textContent == "" {
				textContent = doc.Content
			}
			if textContent == "" {
				if ft, ok := doc.Meta["full_text"].(string); ok && ft != "" {
					textContent = ft
				}
			}
			if textContent == "" {
				if rt, ok := doc.Meta["raw_text"].(string); ok && rt != "" {
					textContent = rt
				}
			}

			// Sanitize UTF-8
			textContent = sanitizeUTF8(textContent)

			// Limit each document's context
			if utf8.RuneCountInString(textContent) > maxContextPerDoc {
				runes := []rune(textContent)
				textContent = string(runes[:maxContextPerDoc]) + "..."
			}

			// Log context being constructed
			log.Printf("📝 Context for %s: %d chars (limited from %d)",
				doc.Title, len(textContent), len(doc.Snippet))

			// Format context with proper source reference
			sourceHeader := ""
			switch doc.Source {
			case "DEKA":
				sourceHeader = fmt.Sprintf("[DEKA] %s (Ref: %s)", doc.Title, doc.FileName)
			case "LAW":
				sourceHeader = fmt.Sprintf("[LAW] %s (File: %s)", doc.Title, doc.FileName)
			default:
				sourceHeader = fmt.Sprintf("[%s] %s", doc.Source, doc.Title)
			}
			contextText += fmt.Sprintf("=== %s ===\n%s\n\n", sourceHeader, textContent)
		}

		// DEBUG: Log all titles being sent to AI
		log.Printf("🔍 Retrieved Documents for RAG:")
		for i, res := range results {
			log.Printf("   [%d] %s (Source: %s, ID: %s)", i+1, res.Title, res.Source, res.ID)
		}

		// Log overall context size
		log.Printf("📚 Total Context Size: %d chars", len(contextText))

		// Create Senior Legal Associate Prompt (The Legal Board V4 - Professional Grade)
		var systemPrompt string

		if intent.Action == "ANSWER" && len(req.History) > 0 {
			// === FOLLOW-UP PROMPT (Conversational: Friendly & Professional) ===
			systemPrompt = `คุณคือ "Sue.AI" ผู้ช่วยกฎหมายที่ "ฉลาด เป็นมืออาชีพ แต่เป็นกันเอง" (Friendly Professional)
หน้าที่ของคุณคือช่วยตอบคำถามต่อยอด ให้คำปรึกษา หรืออธิบายเพิ่มเติมจากข้อมูลที่มีอยู่

**สไตล์การตอบ:**
1. **กระชับ ได้ใจความ (Concise):** ตอบตรงประเด็น ไม่ต้องเกริ่นนำยาวยืด
2. **เป็นกันเอง (Friendly Tone):** ใช้ภาษาที่สุภาพแต่นุ่มนวล เหมือนคุยกับที่ปรึกษาที่ไว้ใจได้ (ไม่ใช่หุ่นยนต์)
3. **มืออาชีพ (Professional):** ข้อมูลกฎหมายต้องแม่นยำ อ้างอิงได้จริง
4. **Context Aware:** ดูบริบทการสนทนาก่อนหน้าเสมอ อย่าตอบซ้ำสิ่งที่เคยตอบไปแล้ว

**ข้อกำหนด:**
- ไม่ต้องสร้าง "Insight Card" หรือ "ตาราง" ซ้ำ (ยกเว้นถูกขอให้ทำ)
- หากมีการอ้างถึงกฎหมายหรือฎีกา ให้ใส่ลิงก์เสมอ: [มาตรา X](cite:law:ชื่อมาตรา) หรือ [ฎีกาที่ X](cite:deka:เลขฎีกา)
- ถ้าคำถามสั้น ให้ตอบสั้นๆ จบใน 2-3 ประโยคถ้าทำได้`
		} else {
			// === FULL ANALYSIS PROMPT (First Turn / New Topic) ===
			systemPrompt = `คุณคือ "Sue.AI" (The Legal Board) ทีมที่ปรึกษากฎหมายอัจฉริยะที่พร้อมดูแลคดีของคุณในทุกมิติ:
1. **Investigator (ตรวจสอบ):** เจาะลึกข้อเท็จจริง ค้นหาจุดอ่อนจุดแข็งของคดี
2. **Prosecutor (ประเมินความเสี่ยง):** วิเคราะห์ความเสี่ยงตามกฎหมายอย่างตรงไปตรงมา
3. **Advocate (วางแผน):** เสนอทางออกและกลยุทธ์การต่อสู้คดีที่ดีที่สุด

=== 🚨 STRICT OPERATIONAL RULES ===
1. **Fact-Based Only:** วิเคราะห์จากข้อมูลที่ได้รับ (Database Context) และประวัติการสนทนา (Conversation Memory) เท่านั้น ห้ามมโนมาตราเอง หากเป็นคำถามต่อเนื่องให้อ้างอิงสิ่งที่เคยคุยกันได้
2. **Identification:** อ่านและระบุเลขมาตราจากเนื้อหาที่ได้รับให้ถูกต้อง
3. **Smart Citations:** สร้างลิงก์ [ชื่อมาตรา](cite:law:ชื่อมาตรา) เฉพาะที่มีข้อมูลจริง
4. **JSON First:** เริ่มต้นด้วย '''json เสมอ
5. **Recency:** เลือกอ้างอิงข้อมูลที่ปีใหม่ที่สุดก่อนเสมอ
6. **Deka Links:** ใช้รูปแบบ [ฎีกาที่ xxx/25xx](cite:deka:เลขฎีกา) เมื่ออ้างถึงฎีกา

=== 📑 RESPONSE STRUCTURE ===
'''json
{
  "type": "insight_card",
  "verdict": "Likely Win / Likely Lose / Uncertain",
  "confidence": "High / Medium / Low",
  "risk_level": "High / Medium / Low",
  "key_law": "มาตราหลักที่ใช้ตัดสิน",
  "win_chance": "โอกาสชนะคดี",
  "summary": "สรุปสั้นๆ 1 ประโยค"
}
'''

### 🏛️ ผลการวิเคราะห์ (The Legal Board Analysis)

**ตารางวิเคราะห์ความเสี่ยง (The Arena Table)**
| ประเด็นข้อเท็จจริง | ความเสี่ยง (Risk) | ข้อต่อสู้ (Defense) |
|---|---|---|

**เจาะลึกข้อกฎหมาย (Legal Deep Dive)**
(อธิบายมาตราสำคัญและแนวคำพิพากษาที่เกี่ยวข้องอย่างเข้าใจง่าย)

**ทางเลือกและกลยุทธ์ (Strategic Options)**
| ทางเลือก (Options) | แผนการดำเนินการ (Action Plan) | ผลลัพธ์/ความเสี่ยง (Outcome & Risk) |
|---|---|---|
| Option A: ... | ... | ... |
| Option B: ... | ... | ... |

**คำแนะนำเพิ่มเติม (Next Steps)**
(สิ่งที่ควรเตรียมตัวหรือหาหลักฐานเพิ่ม)`
		}

		// DEBUG: Print prompt to ensure correct persona
		log.Printf("🤖 System Prompt Preview (First 100 chars): %s...", systemPrompt[:100])

		// Convert History to String
		historyText := ""
		for _, h := range req.History {
			roleName := "User"
			if h["role"] == "assistant" || h["role"] == "model" {
				roleName = "Sue.AI"
			}
			historyText += fmt.Sprintf("%s: %s\n", roleName, h["content"])
		}

		// Combine Prompts with Memory (With Instruction Reminder at the END)
		instructionReminder := ""
		if intent.Action != "ANSWER" {
			instructionReminder = `
=== 🚨 FINAL COMMAND ===
- Start response with '''json block (type: insight_card) IMMEDIATELY.
- RECENCY PRIORITY: อ้างอิงกฎหมายและฎีกา "ปีล่าสุด" เป็นอันดับแรกเสมอ
- FULL CITATION: ระบุมาตราพร้อมชื่อ พ.ร.บ. ทุกครั้ง
- NO headings BEFORE the JSON block.
- Create the Arena Table (Plaintiff vs Defendant).`
		} else {
			instructionReminder = `
=== 🚨 FINAL COMMAND ===
- ตอบคำถามต่อเนื่อง (Follow-up) อย่างเป็นธรรมชาติ
- ไม่ต้องเริ่มด้วย JSON Insight Card
- ใช้ Markdown formatting ให้อ่านง่าย`
		}

		finalPrompt := fmt.Sprintf("%s\n\n=== 📜 ประวัติการสนทนา (Conversation Memory) ===\n%s\n\n=== 📚 ข้อมูลจากฐานข้อมูล (Database Context) ===\n%s\n\n%s\n\nUser Question:\n%s\n\nAnswer:", systemPrompt, historyText, contextText, instructionReminder, req.Question)

		// Configure Model for Precision (Low Temperature)
		h.RAG.GenModel.SetTemperature(0.25)
		h.RAG.GenModel.SetTopP(0.8)
		h.RAG.GenModel.SetTopK(40)

		// Stream Generation with Retry Logic for 429
		var iter *genai.GenerateContentResponseIterator
		maxRetries := 3
		var fullResponse strings.Builder // New: to collect response for logging

		for attempt := 0; attempt < maxRetries; attempt++ {
			iter = h.RAG.GenModel.GenerateContentStream(c.Request.Context(), genai.Text(finalPrompt))

			// Peek for error
			resp, err := iter.Next()
			if err == nil {
				// Success! Push first chunk manually
				if len(resp.Candidates) > 0 && len(resp.Candidates[0].Content.Parts) > 0 {
					if txt, ok := resp.Candidates[0].Content.Parts[0].(genai.Text); ok {
						fullResponse.WriteString(string(txt))
						msg := map[string]string{"type": "chunk", "text": string(txt)}
						msgJSON, _ := json.Marshal(msg)
						fmt.Fprintf(w, "data: %s\n\n", string(msgJSON))
						w.(http.Flusher).Flush()
					}
				}
				break
			}

			// If error is 429, wait and retry
			if strings.Contains(err.Error(), "429") || strings.Contains(err.Error(), "Resource exhausted") {
				log.Printf("⚠️ Rate limit (429) hit, retrying in 2s... (Attempt %d/%d)", attempt+1, maxRetries)
				time.Sleep(2 * time.Second)
				if attempt == maxRetries-1 {
					// FALLBACK: Switch into DEMO MODE if Quota is exhausted
					log.Printf("⚠️ Quota Exhausted! Switching to DEMO MODE.")
					h.streamMockResponse(w)
					return false
				}
				continue
			}

			// Other errors
			log.Printf("❌ Generation Failed: %v", err)
			h.sendError(w, fmt.Sprintf("AI Generation Error: %v", err))
			return false
		}

		for {
			resp, err := iter.Next()
			if err == iterator.Done {
				break
			}
			if err != nil {
				log.Printf("Stream Error: %v", err)
				break
			}

			if len(resp.Candidates) > 0 && len(resp.Candidates[0].Content.Parts) > 0 {
				if txt, ok := resp.Candidates[0].Content.Parts[0].(genai.Text); ok {
					fullResponse.WriteString(string(txt))
					// Send Token in exact format frontend expects (type: chunk, text: content)
					msg := map[string]string{
						"type": "chunk",
						"text": string(txt),
					}
					jsonBytes, _ := json.Marshal(msg)
					fmt.Fprintf(w, "data: %s\n\n", jsonBytes)
					w.(http.Flusher).Flush()
				}
			}
		}

		// FINAL LOGGING: Print what AI actually answered for debugging
		log.Printf("🤖 [AI COMPLETE RESPONSE] 🤖\n%s\n-------------------", fullResponse.String())

		// Send Sources Event (Moved to End per User Request)
		// Frontend expects: { type: 'sources', data: [ ... ] }
		h.sendSSEObject(w, "sources", results)

		// End Stream - MUST SEND RAW "[DONE]" string for frontend check
		// Frontend: if (dataStr.trim() === '[DONE]')
		fmt.Fprintf(w, "data: [DONE]\n\n")
		w.(http.Flusher).Flush()

		return false // Stop connection logic
	})
}

// Helper to format SSE message as standard JSON envelope (for 'sources')
func (h *Handler) sendSSEObject(w io.Writer, eventType string, payload interface{}) {
	msg := map[string]interface{}{
		"type": eventType,
		"data": payload,
	}

	jsonBytes, _ := json.Marshal(msg)
	fmt.Fprintf(w, "data: %s\n\n", jsonBytes)
	if f, ok := w.(http.Flusher); ok {
		f.Flush()
	}
}

func (h *Handler) sendStatus(w io.Writer, message string, mode string) {
	msg := map[string]string{
		"type": "status",
		"text": message,
		"mode": mode,
	}
	jsonBytes, _ := json.Marshal(msg)
	fmt.Fprintf(w, "data: %s\n\n", jsonBytes)
	if f, ok := w.(http.Flusher); ok {
		f.Flush()
	}
}

func (h *Handler) sendError(w io.Writer, errorMsg string) {
	msg := map[string]string{
		"type": "error",
		"text": errorMsg,
	}
	jsonBytes, _ := json.Marshal(msg)
	fmt.Fprintf(w, "data: %s\n\n", jsonBytes)
	if f, ok := w.(http.Flusher); ok {
		f.Flush()
	}
}

// sanitizeUTF8 removes invalid UTF-8 sequences from a string
func sanitizeUTF8(s string) string {
	if utf8.ValidString(s) {
		return s
	}

	// Build a new string with only valid UTF-8 runes
	var builder strings.Builder
	builder.Grow(len(s))

	for i := 0; i < len(s); {
		r, size := utf8.DecodeRuneInString(s[i:])
		if r == utf8.RuneError && size == 1 {
			// Invalid byte, skip it
			i++
			continue
		}
		builder.WriteRune(r)
		i += size
	}

	return builder.String()
}

// Helper to extract conversation ID from history
func getConversationID(history []map[string]string) string {
	if len(history) == 0 {
		return ""
	}
	// The frontend usually appends a system message or includes it in the first message?
	// Actually, based on page.tsx:
	// history.unshift({ role: 'system', content: '', conversation_id: activeConvId } as any);
	// It's in the FIRST message of history array sent from frontend.
	firstMsg := history[0]
	if id, ok := firstMsg["conversation_id"]; ok && id != "" {
		return id
	}
	return ""
}

// streamMockResponse sends a hardcoded useful response for Demo purposes
func (h *Handler) streamMockResponse(w io.Writer) {
	// 1. Simulate "Thinking" delay
	time.Sleep(1 * time.Second)

	// 2. Draft the Mock Answer
	mockAnswer := `'''json
{
  "type": "insight_card",
  "verdict": "Likely Win",
  "confidence": "High",
  "risk_level": "Low",
  "key_law": "ประมวลกฎหมายแพ่งและพาณิชย์ มาตรา 653",
  "win_chance": "85%",
  "summary": "มีหลักฐานเป็นหนังสือกู้ยืมลงลายมือชื่อผู้ยืมชัดเจน สามารถฟ้องร้องบังคับคดีได้ตามกฎหมาย"
}
'''

### 🏛️ การวิเคราะห์โดยคณะทำงานกฎหมาย (Demo Mode)

**ตารางวิเคราะห์ประเด็น (The Arena Table)**
| ประเด็นข้อเท็จจริง | ฝ่ายโจทก์/พนักงานอัยการ (Risk) | ฝ่ายจำเลย/ผู้ถูกกล่าวหา (Defense) |
|---|---|---|
| หลักฐานการกู้ยืม | มีสัญญากู้ยืมและลายมือชื่อผู้ยืมครบถ้วน (Strong Evidence) | อาจต่อสู้เรื่องลายมือชื่อปลอม หรือสัญญากระทำขึ้นโดยมิชอบ (Weak Defense) |
| การชำระหนี้ | ผู้กู้ผิดนัดชำระหนี้ตามกำหนด | อาจอ้างว่าได้ชำระหนี้ไปบ้างแล้วแต่ไม่มีหลักฐาน |

**รายละเอียดทางกฎหมาย (Deep Dive)**
ตาม **ประมวลกฎหมายแพ่งและพาณิชย์ มาตรา 653** การกู้ยืมเงินกว่า 2,000 บาทขึ้นไปนั้น จำเป็นต้องมีหลักฐานเป็นหนังสือลงลายมือชื่อผู้ยืม จึงจะฟ้องร้องบังคับคดีได้
ในกรณีนี้ หากคุณมีสัญญา (Contract) หรือหลักฐานแชทที่ระบุยอดเงินและเจตนาการกู้ยืมชัดเจน ก็ถือว่าเข้าองค์ประกอบกฎหมายแล้ว

**ฎีกาที่เกี่ยวข้อง:**
*   **คำพิพากษาศาลฎีกาที่ 1234/2565:** ศาลวินิจฉัยว่าแม้สัญญาไม่ลงวันที่ แต่มีลายมือชื่อผู้ยืม ก็ถือเป็นหลักฐานที่สมบูรณ์

**กลยุทธ์และทางเลือก (Strategic Options Table)**
| ทางเลือก (Options) | แนวทางการดำเนินการ (Action Plan) | ผลลัพธ์ที่คาดหวัง / ความเสี่ยง (Outcome & Risk) |
|---|---|---|
| **Option A: ยื่นโนติส (Notice)** | ให้ทนายความออกหนังสือทวงถามหนี้อย่างเป็นทางการ | ลูกหนี้อาจกลัวและรีบนำเงินมาคืน (Success Rate: High) |
| **Option B: ฟ้องศาลแพ่ง** | รวบรวมหลักฐานและยื่นฟ้องเรียกเงินต้น+ดอกเบี้ย | ชนะคดีแน่นอน แต่อาจเสียเวลา 6-12 เดือน |

> **หมายเหตุ:** นี่คือ **คำตอบจำลอง (Demo Mode)** เนื่องจากระบบ AI จริงกำลังมีผู้ใช้งานจำนวนมาก กรุณาลองใหม่ภายหลังเพื่อรับคำวิเคราะห์แบบ Real-time ครับ`

	// 3. Stream it out in chunks nicely
	chunkSize := 50
	runes := []rune(mockAnswer)

	for i := 0; i < len(runes); i += chunkSize {
		end := i + chunkSize
		if end > len(runes) {
			end = len(runes)
		}
		chunk := string(runes[i:end])

		msg := map[string]string{
			"type": "chunk",
			"text": chunk,
		}
		jsonBytes, _ := json.Marshal(msg)
		fmt.Fprintf(w, "data: %s\n\n", jsonBytes)
		if f, ok := w.(http.Flusher); ok {
			f.Flush()
		}
		time.Sleep(50 * time.Millisecond) // Typing effect
	}

	// Send Done signal is handled by the caller, but we return, and the caller sends sources then [DONE]
}
