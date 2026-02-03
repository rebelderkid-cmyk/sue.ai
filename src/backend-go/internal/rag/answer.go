package rag

import (
	"context"
	"fmt"
	"log"

	"github.com/google/generative-ai-go/genai"
)

// GenerateAnswer synthesizes the final answer based on retrieved documents
func (s *RAGService) GenerateAnswer(ctx context.Context, query string, docs []SearchResult) (string, error) {
	if len(docs) == 0 {
		return "ไม่พบข้อมูลฏีกาหรือกฎหมายที่เกี่ยวข้องในฐานข้อมูลครับ (No relevant documents found).", nil
	}

	// 1. Construct Context from Documents
	contextText := ""
	for i, doc := range docs {
		// Limit to top 5 docs to fit context window
		if i >= 5 {
			break
		}
		contextText += fmt.Sprintf("Source %d:\nTitle: %s\nSnippet: %s\nFull Text: %s\n\n", i+1, doc.Title, doc.Snippet, doc.Content)
	}

	// 2. Construct Prompt (The Legal Board V3 - Unified Fallback)
	prompt := fmt.Sprintf(`
		Role: You are "Law5 AI", a specialized Assistant for Lawyers (ผู้ช่วยส่วนตัวของทนายความ). 
		Your mission is to provide high-precision legal research, document analysis, and strategic case advice.
        Context Information:
        %s

        User Question: "%s"

        Instructions:
        1. **Investigator:** If facts are missing (5W1H), ask clarifying questions first.
        2. **Prosecutor:** Cite laws & precedents. 
           - **For Deka/Rulings:** Use the Provided Context.
           - **For Laws/Statutes:** If missing from context, use your Internal Knowledge or Internet Search (if available) to verify current Thai Laws.
        3. **Advocate:** Propose Strategic Options (A/B/C) for the user.
        
        Output Format (STRICT):
        1. Use Markdown Headers (##, ###) for clear section hierarchy.
        2. Use Bold (**text**) for important legal concepts and Deka numbers.
        3. Include an "Insight Card" (JSON block) for quick summary.
        4. Include a "Comparison Table" (Markdown) to show conflicting views if applicable.
        5. Use Bullet Points for the "Strategic Options" section.

        Style: Professional, concise, and structured. Use Thai as primary language.
        
        Answer (Must follow strict Markdown structure):
    `, contextText, query)

	// 3. Generate
	resp, err := s.GenModel.GenerateContent(ctx, genai.Text(prompt))
	if err != nil {
		log.Printf("❌ Generation Failed: %v", err)
		return "", err
	}

	if len(resp.Candidates) > 0 && len(resp.Candidates[0].Content.Parts) > 0 {
		if txt, ok := resp.Candidates[0].Content.Parts[0].(genai.Text); ok {
			return string(txt), nil
		}
	}

	return "เกิดข้อผิดพลาดในการประมวลผลคำตอบ (Generation Error)", nil
}
