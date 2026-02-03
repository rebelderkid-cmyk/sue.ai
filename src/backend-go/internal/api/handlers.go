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
	c.Writer.Header().Set("X-Accel-Buffering", "no")

	c.Stream(func(w io.Writer) bool {
		ragCtx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
		defer cancel()

		// 1. Intent Analysis
		analyzer := agent.NewIntentAnalyzer(h.RAG.GenClient)
		intent, clsErr := analyzer.Classify(ragCtx, req.History, req.Question)
		if clsErr != nil {
			log.Printf("⚠️ Intent Classification failed: %v. Defaulting to SEARCH.", clsErr)
			intent = agent.IntentResult{Action: "SEARCH", Reason: "Error"}
		}
		log.Printf("🧠 Agent Decision: %s (Reason: %s)", intent.Action, intent.Reason)

		skipSearch := intent.Action == "ANSWER"

		// 2. Retrieve Context (Search RAG or Use Memory)
		var results []rag.SearchResult
		var searchErr error

		if !skipSearch {
			h.sendStatus(w, "กำลังสืบค้นข้อมูล...", "SEARCH")
			optimizedQueries := h.RAG.OptimizeQueries(ragCtx, req.Question)
			results, searchErr = h.RAG.Search(ragCtx, optimizedQueries, req.Filters)
			if searchErr != nil {
				log.Printf("❌ Search Error: %v", searchErr)
				h.sendStatus(w, "ค้นหาขัดข้อง กำลังพยายามตอบจากความรู้ที่มี...", "ANSWER")
			} else {
				if convID := getConversationID(req.History); convID != "" {
					memory.GetMemory().SaveContext(convID, results)
				}
			}
		} else {
			h.sendStatus(w, "กำลังทบทวนความจำ...", "ANSWER")
			if convID := getConversationID(req.History); convID != "" {
				cachedResults := memory.GetMemory().GetContext(convID)
				if cachedResults != nil {
					results = cachedResults
				}
			}
		}

		h.sendStatus(w, "กำลังเรียบเรียงคำตอบ...", "ANSWER")

		// 3. Construct Context String
		startGen := time.Now()
		contextText := ""
		// OPTIMIZATION: Reduced Limits for Faster Response ⚡️
		maxContextPerDoc := 2000 // Reduced from 10,000 to Speed up!
		if req.DeepSearch {
			maxContextPerDoc = 5000 // Reduced from 50,000
		}

		// Reorder: LAW first, then DEKA
		var contextDocs []rag.SearchResult
		for _, doc := range results {
			if doc.Source == "LAW" {
				contextDocs = append(contextDocs, doc)
			}
		}
		for _, doc := range results {
			if doc.Source != "LAW" {
				contextDocs = append(contextDocs, doc)
			}
		}

		limit := 5 // Reduced from 12 to 5 (Focus on Top Results)
		for i, doc := range contextDocs {
			if i >= limit {
				break
			}
			textContent := doc.Snippet

			// Strategy: Use Snippet if available and meaningful length (> 200 chars)
			// Otherwise fallback to Smart Content Truncation
			if len(textContent) < 200 {
				fullContent := doc.Content
				if ft, ok := doc.Meta["full_text"].(string); ok && len(ft) > len(fullContent) {
					fullContent = ft
				}

				// Smart Truncate: Head (Facts) + Tail (Ruling)
				// Deka structure is usually Facts -> Reasoning -> Ruling
				runes := []rune(sanitizeUTF8(fullContent))
				totalLen := len(runes)

				if totalLen > maxContextPerDoc {
					// Take first 40% of quota for Head, last 60% for Tail (Rules usually at end)
					headLen := int(float64(maxContextPerDoc) * 0.4)
					tailLen := maxContextPerDoc - headLen

					if totalLen > (headLen + tailLen + 100) {
						textContent = string(runes[:headLen]) + "\n...[เนื้อหาถูกย่อ]...\n" + string(runes[totalLen-tailLen:])
					} else {
						textContent = string(runes)
					}
				} else {
					textContent = fullContent
				}
			}

			// Final Safety check
			if utf8.RuneCountInString(textContent) > maxContextPerDoc+200 {
				runes := []rune(textContent)
				textContent = string(runes[:maxContextPerDoc]) + "..."
			}

			sourceHeader := fmt.Sprintf("[%s] %s (ID: %s)", doc.Source, doc.Title, doc.ID)
			contextText += fmt.Sprintf("=== %s ===\n%s\n\n", sourceHeader, textContent)
		}

		log.Printf("⏱️ Context Prepared in %v. Total Length: %d chars", time.Since(startGen), len(contextText))

		// 4. Construct System Prompt (Natural & Flexible with Deep Legal Insight)
		systemPrompt := `Role: You are "Sue.AI", an elite Senior Legal Advisor. 
Tone: Professional, empathetic, confident, and highly articulate. You speak naturally like a human expert ensuring the client understands the legal landscape.

GOAL: Provide strategic, fact-based legal advice that naturally integrates case laws (Deka) and legal principles.

CORE INSTRUCTIONS:
1. **Natural Integration of Law:** Do NOT simply list laws. Instead, weave them into your explanation.
   - *Bad:* "According to Section 575..."
   - *Good:* "In this situation, the law (Section 575) actually protects you because..."
2. **Case Law Comparison (Crucial):**
   - You MUST cite relevant Supreme Court Rulings (Deka) to support your points.
   - **Compare outcomes:** "Similar to [Deka 1234/2560](cite:deka:1234/2560), the court ruled in favor of the employee because..." VS "However, in [Deka 999/2561](cite:deka:999/2561), the employer won because they had clear evidence of..."
   - Use these comparisons to show *nuance* and *risk*.
3. **Smart Citations:** EVERY time you mention a Law or Deka, you MUST hyperlink it:
   - Law: [Section X](cite:law:Name)
   - Deka: [Deka X/25XX](cite:deka:ID)
4. **Structured but Natural:** Use paragraphs and bullet points for readability, but keep the flow conversational.

LANGUAGE RULES:
- **Detect Language:** If User asks in Thai -> Answer in **THAI**. If English -> Answer in **ENGLISH**.
- **Translation:** Explain legal terms clearly in the target language.`

		// Convert History
		historyText := ""
		for _, h := range req.History {
			roleName := "User"
			if h["role"] == "assistant" || h["role"] == "model" {
				roleName = "Sue.AI"
			}
			historyText += fmt.Sprintf("%s: %s\n", roleName, h["content"])
		}

		// Final Prompt Assembly
		finalPrompt := fmt.Sprintf("%s\n\n=== 📜 MEMORY ===\n%s\n\n=== 📚 DATABASE CONTEXT ===\n%s\n\nUser Question:\n%s\n\nAnswer (Natural & Professional):", systemPrompt, historyText, contextText, req.Question)

		// Configure Model
		h.RAG.GenModel.SetTemperature(0.3) // Slightly higher for natural flow
		h.RAG.GenModel.SetTopP(0.85)

		// Stream Generation
		var iter *genai.GenerateContentResponseIterator
		var fullResponse strings.Builder

		iter = h.RAG.GenModel.GenerateContentStream(c.Request.Context(), genai.Text(finalPrompt))

		for {
			resp, err := iter.Next()
			if err == iterator.Done {
				break
			}
			if err != nil {
				log.Printf("Stream Error: %v", err)
				h.sendError(w, fmt.Sprintf("AI Error: %v", err))
				return false
			}

			if len(resp.Candidates) > 0 && len(resp.Candidates[0].Content.Parts) > 0 {
				if txt, ok := resp.Candidates[0].Content.Parts[0].(genai.Text); ok {
					chunk := string(txt)
					fullResponse.WriteString(chunk)
					msg := map[string]string{"type": "chunk", "text": chunk}
					jsonBytes, _ := json.Marshal(msg)
					fmt.Fprintf(w, "data: %s\n\n", jsonBytes)
					w.(http.Flusher).Flush()
				}
			}
		}

		// Finalize
		log.Printf("🤖 RESPONSE:\n%s", fullResponse.String())
		h.sendSSEObject(w, "sources", results)
		fmt.Fprintf(w, "data: [DONE]\n\n")
		w.(http.Flusher).Flush()

		return false
	})
}

// Helpers... (Keeping existing helpers)
func (h *Handler) sendSSEObject(w io.Writer, eventType string, payload interface{}) {
	msg := map[string]interface{}{"type": eventType, "data": payload}
	jsonBytes, _ := json.Marshal(msg)
	fmt.Fprintf(w, "data: %s\n\n", jsonBytes)
	if f, ok := w.(http.Flusher); ok {
		f.Flush()
	}
}

func (h *Handler) sendStatus(w io.Writer, message string, mode string) {
	msg := map[string]string{"type": "status", "text": message, "mode": mode}
	jsonBytes, _ := json.Marshal(msg)
	fmt.Fprintf(w, "data: %s\n\n", jsonBytes)
	if f, ok := w.(http.Flusher); ok {
		f.Flush()
	}
}

func (h *Handler) sendError(w io.Writer, errorMsg string) {
	msg := map[string]string{"type": "error", "text": errorMsg}
	jsonBytes, _ := json.Marshal(msg)
	fmt.Fprintf(w, "data: %s\n\n", jsonBytes)
	if f, ok := w.(http.Flusher); ok {
		f.Flush()
	}
}

func sanitizeUTF8(s string) string {
	if utf8.ValidString(s) {
		return s
	}
	var builder strings.Builder
	builder.Grow(len(s))
	for i := 0; i < len(s); {
		r, size := utf8.DecodeRuneInString(s[i:])
		if r == utf8.RuneError && size == 1 {
			i++
			continue
		}
		builder.WriteRune(r)
		i += size
	}
	return builder.String()
}

func getConversationID(history []map[string]string) string {
	if len(history) == 0 {
		return ""
	}
	firstMsg := history[0]
	if id, ok := firstMsg["conversation_id"]; ok && id != "" {
		return id
	}
	return ""
}
