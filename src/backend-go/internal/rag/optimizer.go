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
Task: แปลงคำถามของผู้ใช้เป็น 2 SEARCH QUERIES แยกกันเพื่อใช้ใน RAG System ของ Google Vertex Search

คำถามเดิม: "%s"

=== หลักการสร้างคำค้นหา (Searching Principles) ===

1. **DEKA_QUERY** (สำหรับค้นหาคำพิพากษาศาลฎีกา):
   - เน้น "คำสำคัญทางกฎหมาย" (Legal Keywords) และ "ข้อเท็จจริงหลัก" (Key Facts)
   - ตัดคำฟุ่มเฟือยออก ให้เหลือแต่ใจความสำคัญ เพื่อให้ Search Engine ทำงานได้ดีที่สุด
   - **ข้อห้าม**: ห้ามใส่คำว่า "ปีล่าสุด", "พ.ศ.", "ปัจจุบัน" หรือระบุปี พ.ศ. ลงไปใน Query (เพราะจะทำให้ Search Engine กรองผิด จนหาไม่เจอ)
   - ตัวอย่าง: "ฉ้อโกง บรรยายฟ้อง ไม่สุจริต หลอกลวง" (ถูกต้อง)
   - ตัวอย่างผิด: "ฎีกาฉ้อโกงปีล่าสุด 2567" (ผิด)

2. **LAW_QUERY** (สำหรับกฎหมาย):
   - **ชื่อกฎหมาย**: ระบุชื่อกฎหมายที่เกี่ยวข้องให้ชัดเจน
   - **มาตรา**: ถ้าทราบ หรือคาดเดาได้ ให้ระบุเลขมาตรา
   - **ตัวอย่าง**: "ประมวลกฎหมายอาญา มาตรา 288 289 ฆ่าผู้อื่น", "พ.ร.บ.อาวุธปืน"

Guidelines:
- DEKA_QUERY: ขอ keywords เน้นๆ 3-5 คำ ที่ตรงประเด็นที่สุด
- LAW_QUERY: ขอชื่อกฎหมายที่ถูกต้องและมาตราที่เกี่ยวข้อง
- Output เฉพาะผลลัพธ์ตาม Format เท่านั้น

Output Format:
DEKA: [query สำหรับศาลฎีกา]
LAW: [query สำหรับกฎหมาย]
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
			log.Printf("🔹 DEKA Optimized: %s", queries.DekaQuery)
			log.Printf("🔹 LAW Optimized: %s", queries.LawQuery)
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
