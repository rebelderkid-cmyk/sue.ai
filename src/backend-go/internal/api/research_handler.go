package api

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/generative-ai-go/genai"
)

// ResearchRequest structure
type ResearchRequest struct {
	Query string `json:"query" binding:"required"`
}

// CaseSummary defines the structure for the AI-generated table row
type CaseSummary struct {
	CaseID        string `json:"case_id"`
	Year          string `json:"year"`
	Facts         string `json:"facts"`          // ข้อเท็จจริงย่อ
	LegalIssue    string `json:"legal_issue"`    // ประเด็นข้อกฎหมาย
	Ruling        string `json:"ruling"`         // คำวินิจฉัยย่อ
	Reasoning     string `json:"reasoning"`      // เหตุผลประกอบ (สั้นๆ)
	LawyerOpinion string `json:"lawyer_opinion"` // ความเห็น/กลยุทธ์สำหรับทนาย
}

// ResearchHandler handles the contextual search & table summary request
func (h *Handler) ResearchHandler(c *gin.Context) {
	var req ResearchRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.sendError(c.Writer, "Invalid request body")
		return
	}

	// 1. Search for Relevant Cases
	log.Printf("🔍 Researching: %s", req.Query)

	ctx := c.Request.Context()

	// Optimize the query first
	optimizedQueries := h.RAG.OptimizeQueries(ctx, req.Query)

	// Perform Search - fetch more candidates (15) to let AI filter the best 5
	searchResults, err := h.RAG.Search(ctx, optimizedQueries, nil)
	if err != nil {
		h.sendError(c.Writer, fmt.Sprintf("Search failed: %v", err))
		return
	}

	// Dynamic Truncate & Filter Candidates
	var candidateContexts []string
	limit := 10 // Reduce from 15 to 10 for speed
	if len(searchResults) < limit {
		limit = len(searchResults)
	}

	for i := 0; i < limit; i++ {
		doc := searchResults[i]
		// Limit content length to save tokens (approx 800 chars per doc for selection phase)
		content := doc.Content
		if len(content) > 800 {
			content = content[:800] + "...(truncated)"
		}
		// Include Date/Year info explicitly if available in metadata, otherwise rely on Title/Content
		candidateContexts = append(candidateContexts, fmt.Sprintf("CANDIDATE #%d (ID: %s):\n%s", i+1, doc.Title, content))
	}

	fullContext := strings.Join(candidateContexts, "\n\n----------------\n\n")

	// 2. Construct Prompt for Intelligent Selection & Table Generation
	systemPrompt := `You are an expert Senior Legal Advisor specializing in Thai Law.
Your goal is to assist a lawyer by selecting and summarizing the most relevant case laws (Deka).

TASK:
1. Review the provided 10 candidate cases.
2. **SELECT only the TOP 5 cases** based on these criteria:
   - **Recency:** Prioritize the most recent cases (Newest Year).
   - **Diversity:** Try to include cases with different outcomes (e.g., Employer wins vs. Employee wins) to show the full legal landscape.
3. For the selected 5 cases, generate a comparison table JSON.

LANGUAGE RULES (Critical):
- **Detect the language of the User's Search Query.**
- If the User asks in **THAI**, respond entirely in **THAI**.
- If the User asks in **ENGLISH**, respond entirely in **ENGLISH** (translate facts, issues, rulings, etc.).

OUTPUT FORMAT (JSON Array):
[
  {
    "case_id": "1234/2565",
    "year": "2565",
    "facts": "Brief facts of the case...",
    "legal_issue": "Main legal question...",
    "ruling": "The court's decision...",
    "reasoning": "Key legal reasoning...",
    "lawyer_opinion": "Strategic advice for the lawyer..."
  }
]

RULES:
- Output MUST be valid JSON only.`

	userPrompt := fmt.Sprintf("Search Query: \"%s\"\n\nCandidate Cases:\n%s", req.Query, fullContext)

	// 3. Generate Content using Gemini
	h.RAG.GenModel.SetTemperature(0.2) // Slightly higher temp for creative selection

	resp, err := h.RAG.GenModel.GenerateContent(ctx,
		genai.Text(systemPrompt),
		genai.Text(userPrompt),
	)
	if err != nil {
		h.sendError(c.Writer, fmt.Sprintf("Analysis failed: %v", err))
		return
	}

	// Log Token Usage
	if resp.UsageMetadata != nil {
		log.Printf("💰 Research Request Cost: Input=%d, Output=%d, Total=%d Tokens",
			resp.UsageMetadata.PromptTokenCount,
			resp.UsageMetadata.CandidatesTokenCount,
			resp.UsageMetadata.TotalTokenCount,
		)
	}

	// 4. Parse & Clean Output
	if len(resp.Candidates) == 0 || len(resp.Candidates[0].Content.Parts) == 0 {
		h.sendError(c.Writer, "AI returned empty response")
		return
	}

	rawJSON := ""
	if txt, ok := resp.Candidates[0].Content.Parts[0].(genai.Text); ok {
		rawJSON = string(txt)
	}

	// Clean Markdown
	rawJSON = strings.TrimSpace(rawJSON)
	if strings.HasPrefix(rawJSON, "```json") {
		rawJSON = strings.TrimPrefix(rawJSON, "```json")
		rawJSON = strings.TrimSuffix(rawJSON, "```")
	} else if strings.HasPrefix(rawJSON, "```") {
		rawJSON = strings.TrimPrefix(rawJSON, "```")
		rawJSON = strings.TrimSuffix(rawJSON, "```")
	}

	// Validate JSON
	var summaries []CaseSummary
	if err := json.Unmarshal([]byte(rawJSON), &summaries); err != nil {
		log.Printf("❌ JSON Parse Error: %v\nRaw Output: %s", err, rawJSON)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to parse AI response",
			"raw":   rawJSON,
		})
		return
	}

	// 5. Return Success Response
	c.JSON(http.StatusOK, gin.H{
		"query":     req.Query,
		"results":   summaries,
		"timestamp": time.Now(),
	})
}
