package rag

import (
	"context"
	"fmt"
	"log"
	"strings"

	"github.com/google/generative-ai-go/genai"
)

// OptimizedQueries contains separate queries for each search engine
type OptimizedQueries struct {
	DekaQuery string // For searching case law (คำพิพากษาศาลฎีกา)
	LawQuery  string // For searching statutes (ตัวบทกฎหมาย)
	Category  string // Identified category: civil, criminal, labor, procedure, general
}

// SmartQueryOptimizer rewrites user queries into TWO specialized queries
func (s *RAGService) OptimizeQueries(ctx context.Context, userQuestion string) OptimizedQueries {
	prompt := fmt.Sprintf(`
Role: คุณเป็นผู้เชี่ยวชาญด้านการค้นหาข้อมูลกฎหมายไทย (Expert Legal Search Operator)
Task: แปลงคำถามของผู้ใช้เป็น 2 SEARCH QUERIES แยกกันเพื่อใช้ใน RAG System

คำถามเดิม: "%s"

=== หลักการสร้างคำค้นหา (Searching Principles) ===

1. **DEKA_QUERY** (สำหรับค้นหาคำพิพากษาศาลฎีกา):
   - เน้นคำค้นหาที่เกี่ยวข้องกับ "บรรทัดฐาน" และ "ข้อเท็จจริง"
   - **ความสดใหม่ (Recency)**: ใส่คำว่า "ปีล่าสุด" หรือ "ปัจจุบัน" เพื่อให้ได้บรรทัดฐานที่ทันสมัยที่สุด
   - ตัวอย่าง: "ฎีกา ฉ้อโกง บรรยายฟ้อง ไม่สุจริต ปีล่าสุด 2567"

2. **LAW_QUERY** (สำหรับกฎหมาย - สำคัญมาก!):
   - **ลำดับศักดิ์กฎหมาย (Hierarchy)**: เรียงลำดับจาก รัฐธรรมนูญ > ประมวลกฎหมาย > พ.ร.บ. > พ.ร.ฎ. > กฎกระทรวง
   - **ความสดใหม่ (Recency)**: เน้นการค้นหาปีปัจจุบันหรือปีล่าสุดเพื่อให้ได้ข้อมูลที่อัปเดตที่สุด
   - **สถานะ (Validity)**: เน้นหาฉบับที่ "แก้ไขเพิ่มเติมล่าสุด" และระวังฉบับที่ "ถูกยกเลิก"
   - **ตัวอย่าง**: "พ.ร.บ. กู้ยืมเงินที่เป็นการฉ้อโกงประชาชน ฉบับล่าสุด ปี 2567" หรือ "ประมวลกฎหมายอาญา มาตรา 341 ล่าสุด"

Guidelines:
- ห้ามใช้คำฟุ่มเฟือย
- ใส่คำว่า "ฉบับล่าสุด" หรือ "ปีล่าสุด" ใน LAW_QUERY เสมอถ้าเป็นไปได้
- Output เฉพาะผลลัพธ์ตาม Format เท่านั้น

Output Format:
DEKA: [query สำหรับศาลฎีกา]
LAW: [query สำหรับกฎหมายล่าสุด]
CATEGORY: [civil|criminal|labor|procedure|general]
`, userQuestion)

	resp, err := s.GenModel.GenerateContent(ctx, genai.Text(prompt))
	if err != nil {
		log.Printf("⚠️ Optimization Failed: %v", err)
		return OptimizedQueries{DekaQuery: userQuestion, LawQuery: userQuestion}
	}

	if len(resp.Candidates) > 0 && len(resp.Candidates[0].Content.Parts) > 0 {
		if txt, ok := resp.Candidates[0].Content.Parts[0].(genai.Text); ok {
			output := string(txt)
			output = strings.ReplaceAll(output, "\"", "")
			output = strings.ReplaceAll(output, "'", "")
			output = strings.ReplaceAll(output, "`", "")

			// Parse the output
			queries := parseOptimizedQueries(output, userQuestion)
			log.Printf("🔹 DEKA Query: %s", queries.DekaQuery)
			log.Printf("🔹 LAW Query: %s", queries.LawQuery)
			return queries
		}
	}

	return OptimizedQueries{DekaQuery: userQuestion, LawQuery: userQuestion}
}

// parseOptimizedQueries extracts DEKA, LAW, and CATEGORY queries from AI output
func parseOptimizedQueries(output string, fallback string) OptimizedQueries {
	result := OptimizedQueries{DekaQuery: fallback, LawQuery: fallback, Category: "general"}

	lines := strings.Split(output, "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		upperLine := strings.ToUpper(line)

		if strings.HasPrefix(upperLine, "DEKA:") {
			query := strings.TrimSpace(line[5:])
			if query != "" {
				result.DekaQuery = query
			}
		} else if strings.HasPrefix(upperLine, "LAW:") {
			query := strings.TrimSpace(line[4:])
			if query != "" {
				result.LawQuery = query
			}
		} else if strings.HasPrefix(upperLine, "CATEGORY:") {
			cat := strings.ToLower(strings.TrimSpace(line[9:]))
			if cat != "" {
				result.Category = cat
			}
		}
	}

	return result
}

// OptimizeQuery (legacy - single query) for backwards compatibility
func (s *RAGService) OptimizeQuery(ctx context.Context, userQuestion string) string {
	queries := s.OptimizeQueries(ctx, userQuestion)
	// Return DEKA query as default for legacy usage
	return queries.DekaQuery
}
