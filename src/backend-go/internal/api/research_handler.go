package api

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strings"
	"sue-ai-backend/internal/rag"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/generative-ai-go/genai"
)

// ResearchRequest structure
type ResearchRequest struct {
	Query string `json:"query" binding:"required"`
	Page  int    `json:"page"` // 0-based index
}

// CaseSummary defines the structure for the AI-generated table row
type CaseSummary struct {
	CaseID        string `json:"case_id"`
	Year          string `json:"year"`
	Facts         string `json:"facts"`
	LegalIssue    string `json:"legal_issue"`
	Ruling        string `json:"ruling"`
	Reasoning     string `json:"reasoning"`
	LawyerOpinion string `json:"lawyer_opinion"`
	PdfURL        string `json:"pdf_url"`
}

// ResearchHandler handles the contextual search with Batch Streaming for Order Guarantee
func (h *Handler) ResearchHandler(c *gin.Context) {
	c.Writer.Header().Set("Content-Type", "text/event-stream")
	c.Writer.Header().Set("Cache-Control", "no-cache")
	c.Writer.Header().Set("Connection", "keep-alive")
	c.Writer.Header().Set("Transfer-Encoding", "chunked")

	var mu sync.Mutex
	sendEvent := func(eventType string, data interface{}) {
		mu.Lock()
		defer mu.Unlock()
		jsonData, _ := json.Marshal(data)
		fmt.Fprintf(c.Writer, "event: %s\ndata: %s\n\n", eventType, jsonData)
		c.Writer.Flush()
	}

	var req ResearchRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		return
	}

	limit := 5
	offset := req.Page * limit

	log.Printf("⏱️ [START] Research: %s (Page: %d)", req.Query, req.Page)
	sendEvent("status", gin.H{"message": "🔍 กำลังประมวลผลคำค้นหา..."})

	ctx := c.Request.Context()
	optimizePrompt := h.RAG.OptimizeQueries(ctx, req.Query)

	// 1. Search (Fetch pool)
	fetchLimit := 100
	searchResults, err := h.RAG.Search(ctx, optimizePrompt, map[string]interface{}{"limit": fetchLimit})
	if err != nil {
		sendEvent("error", gin.H{"message": "Search failed"})
		return
	}

	// 2. Pagination
	if offset >= len(searchResults) {
		sendEvent("done", gin.H{"message": "No more results"})
		return
	}
	end := offset + limit
	if end > len(searchResults) {
		end = len(searchResults)
	}

	targetDocs := searchResults[offset:end]
	if len(targetDocs) == 0 {
		sendEvent("done", gin.H{"message": "No results found"})
		return
	}

	sendEvent("status", gin.H{"message": fmt.Sprintf("⚡️ ตรวจพบ %d ฎีกาที่เกี่ยวข้อง กำลังวิเคราะห์เชิงลึก...", len(targetDocs))})

	// 3. Parallel AI Generation but collected in order
	results := make([]CaseSummary, len(targetDocs))
	var wg sync.WaitGroup

	for i, doc := range targetDocs {
		wg.Add(1)
		go func(idx int, document rag.SearchResult) {
			defer wg.Done()

			content := document.Content
			if len(content) > 3000 {
				runes := []rune(content)
				if len(runes) > 2000 {
					content = string(runes[:1000]) + "\n...\n" + string(runes[len(runes)-1000:])
				}
			}

			prompt := fmt.Sprintf(`Analyze this Thai Deka Case.
CASE: %s (ID: %s)
CONTENT: %s

OUTPUT JSON ONLY:
{
	"case_id": "%s",
	"year": "%s",
	"facts": "Summarize facts < 2 sentences",
	"legal_issue": "Main legal issue < 1 sentence",
	"ruling": "Ruling < 2 sentences",
	"reasoning": "Reasoning < 2 sentences",
	"lawyer_opinion": "Key strategy/takeaway for lawyer"
}
Key Rules: Respond in THAI. Valid JSON.`, document.ID, content, document.ID, document.Year)

			genCtx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
			defer cancel()

			genResp, genErr := h.RAG.GenModel.GenerateContent(genCtx, genai.Text(prompt))

			summary := CaseSummary{
				CaseID: document.ID,
				Year:   document.Year,
				PdfURL: document.Link,
			}
			if summary.CaseID == "" || strings.Contains(summary.CaseID, "Deka_") {
				summary.CaseID = document.Title
			}

			success := false
			if genErr == nil && len(genResp.Candidates) > 0 {
				if txtPart, ok := genResp.Candidates[0].Content.Parts[0].(genai.Text); ok {
					txt := string(txtPart)
					txt = strings.TrimSpace(txt)
					txt = strings.ReplaceAll(txt, "```json", "")
					txt = strings.ReplaceAll(txt, "```", "")

					var parsed map[string]string
					if json.Unmarshal([]byte(txt), &parsed) == nil {
						summary.Facts = parsed["facts"]
						summary.LegalIssue = parsed["legal_issue"]
						summary.Ruling = parsed["ruling"]
						summary.Reasoning = parsed["reasoning"]
						summary.LawyerOpinion = parsed["lawyer_opinion"]
						if v, ok := parsed["case_id"]; ok && len(v) < 50 {
							summary.CaseID = v
						}
						success = true
					}
				}
			}

			if !success {
				summary.Facts = document.Snippet
				summary.LawyerOpinion = "AI ไม่สามารถสรุปข้อมูลได้ในขณะนี้"
			}

			results[idx] = summary

		}(i, doc)
	}

	// Wait for ALL AI analysis to finish
	wg.Wait()

	// 4. Send items in strict chronological order
	for _, summary := range results {
		sendEvent("result_item", summary)
	}

	sendEvent("done", gin.H{"message": "Page Complete"})
}
