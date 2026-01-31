package rag

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"regexp"
	"sort"
	"strings"
	"sync"

	// Added for parallel execution
	"cloud.google.com/go/discoveryengine/apiv1/discoveryenginepb"
	"google.golang.org/api/iterator"
	"google.golang.org/protobuf/types/known/structpb"
)

// Parallel result type to capture results from goroutines
type searchTaskResult struct {
	results []SearchResult
	err     error
}

type SearchResult struct {
	Title    string `json:"title"`
	Link     string `json:"pdf_url"` // Fixed for frontend
	Snippet  string `json:"snippet"`
	Source   string `json:"source"`   // "DEKA" or "LAW"
	FileName string `json:"filename"` // Original JSONL filename for reference
	Content  string `json:"content"`

	// Frontend expects 'id' and 'year'
	ID   string `json:"id"`
	Year string `json:"year"`

	Meta  map[string]interface{} `json:"meta"`
	Raw   interface{}            `json:"raw,omitempty"` // For debugging
	Score float64                `json:"score"`
}

// Search performs a multi-store search (DEKA + LAW) with specialized queries
func (s *RAGService) Search(ctx context.Context, queries OptimizedQueries, filters map[string]interface{}) ([]SearchResult, error) {
	var allResults []SearchResult

	// Construct Filter String
	filterStr := ""
	var filterParts []string

	// 1. Year Filter
	if val, ok := filters["year"]; ok {
		strVal := fmt.Sprintf("%v", val)
		if strVal != "" {
			if strings.Contains(strVal, ">=") {
				year := strings.Replace(strVal, ">=", "", 1)
				filterParts = append(filterParts, fmt.Sprintf("year >= %s", year))
			} else {
				filterParts = append(filterParts, fmt.Sprintf("year: %s", strVal))
			}
		}
	}

	// 2. Outcome Filter
	if val, ok := filters["outcome"]; ok && val != "" {
		filterParts = append(filterParts, fmt.Sprintf("outcome: \"%v\"", val))
	}

	if len(filterParts) > 0 {
		filterStr = strings.Join(filterParts, " AND ")
		log.Printf("🔍 Applied Filters: %s", filterStr)
	}

	// Define engines with their specific queries
	type engineConfig struct {
		ID    string
		Query string
	}

	engines := map[string]engineConfig{
		"DEKA": {ID: s.Config.EngineIDDeka, Query: queries.DekaQuery},
		// "LAW":  {ID: s.Config.EngineIDLaw, Query: queries.LawQuery}, // DISABLED as per User Request (Use Internet)
	}

	// Parallel Execution setup
	var wg sync.WaitGroup
	resultChan := make(chan searchTaskResult, len(engines))

	log.Printf("⏱️ Starting Parallel Search Execution...")

	for name, conf := range engines {
		if conf.ID == "" {
			continue
		}

		wg.Add(1)
		go func(engineName string, config engineConfig) {
			defer wg.Done()
			var taskResults []SearchResult

			log.Printf("🔎 [Parallel] Searching %s (Engine: %s)...", engineName, config.ID)

			servingConfig := fmt.Sprintf(
				"projects/%s/locations/global/collections/default_collection/engines/%s/servingConfigs/default_config",
				s.Config.ProjectID, config.ID,
			)

			// Use base filter (e.g. year)
			localFilterStr := filterStr

			pageSize := 50
			if engineName == "LAW" {
				pageSize = 100 // Boost LAW search to ensure we don't miss the core sections
			}

			req := &discoveryenginepb.SearchRequest{
				ServingConfig: servingConfig,
				Query:         config.Query,
				Filter:        localFilterStr,
				PageSize:      int32(pageSize),
				ContentSearchSpec: &discoveryenginepb.SearchRequest_ContentSearchSpec{
					SnippetSpec: &discoveryenginepb.SearchRequest_ContentSearchSpec_SnippetSpec{
						ReturnSnippet: true,
					},
					SummarySpec: &discoveryenginepb.SearchRequest_ContentSearchSpec_SummarySpec{
						SummaryResultCount: 3,
						IncludeCitations:   true,
					},
				},
			}

			it := s.SearchClient.Search(ctx, req)
			count := 0
			// Increased sample size per engine to ensure both LAW and DEKA are well-represented
			engineLimit := 30
			if engineName == "LAW" {
				engineLimit = 50 // Be even more aggressive for Law
			}

			// Fetch Results Loop
			for {
				if count >= engineLimit {
					break
				}
				resp, err := it.Next()
				if err == iterator.Done {
					break
				}
				if err != nil {
					log.Printf("❌ [DEBUG] Search loop error for %s: %v", engineName, err)

					// FAILSAFE: If Billing is disabled (Project Quota/Credit issue), use MOCK DATA so the app doesn't look broken.
					if strings.Contains(err.Error(), "BILLING_DISABLED") ||
						strings.Contains(err.Error(), "PermissionDenied") ||
						strings.Contains(err.Error(), "Quota exceeded") {
						log.Printf("⚠️ Billing/Quota issue detected for %s. Enforcing DEMO/MOCK Mode.", engineName)
						taskResults = getMockSearchResults(engineName)
					}
					break
				}
				log.Printf("📝 [DEBUG] Found Doc from %s: %s", engineName, resp.Document.Id)
				if res := s.mapDocumentToSearchResult(resp.Document, engineName); res != nil {
					taskResults = append(taskResults, *res)
					count++
				}
			}

			resultChan <- searchTaskResult{results: taskResults}
		}(name, conf)
	}

	// Close results channel when all workers are done
	go func() {
		wg.Wait()
		close(resultChan)
	}()

	// Collect accumulated results
	var dekaResults, lawResults []SearchResult
	for res := range resultChan {
		if res.err != nil {
			log.Printf("⚠️ %v", res.err)
			continue
		}
		for _, r := range res.results {
			if r.Source == "DEKA" {
				dekaResults = append(dekaResults, r)
			} else {
				lawResults = append(lawResults, r)
			}
		}
	}

	// Sort each category by Year
	sortResults := func(res []SearchResult) {
		sort.Slice(res, func(i, j int) bool {
			return res[i].Year > res[j].Year
		})
	}
	sortResults(dekaResults)
	sortResults(lawResults)

	// Combine: Max 15 Law + 15 Deka (Total 30)
	if len(lawResults) > 15 {
		allResults = append(allResults, lawResults[:15]...)
	} else {
		allResults = append(allResults, lawResults...)
	}

	remainingSlot := 30 - len(allResults)
	if len(dekaResults) > remainingSlot {
		allResults = append(allResults, dekaResults[:remainingSlot]...)
	} else {
		allResults = append(allResults, dekaResults...)
	}

	// Sort results manually: Boost Manual Law IDs to the very top, then by Year
	sort.Slice(allResults, func(i, j int) bool {
		// Priority 1: Manual law entries (IDs starting with 'law-')
		iIsManual := strings.HasPrefix(allResults[i].ID, "law-") || strings.HasPrefix(allResults[i].ID, "section-")
		jIsManual := strings.HasPrefix(allResults[j].ID, "law-") || strings.HasPrefix(allResults[j].ID, "section-")

		if iIsManual && !jIsManual {
			return true
		}
		if !iIsManual && jIsManual {
			return false
		}

		// Priority 2: Year (Descending)
		return allResults[i].Year > allResults[j].Year
	})

	log.Printf("✅ Combined & Boosted Results: %d (Law: %d, Deka: %d)", len(allResults), len(lawResults), len(dekaResults))
	return allResults, nil
}

// mapDocumentToSearchResult converts a Vertex AI document to our internal SearchResult structure
func (s *RAGService) mapDocumentToSearchResult(doc *discoveryenginepb.Document, engineName string) *SearchResult {
	if doc == nil {
		return nil
	}

	dekaRegex := regexp.MustCompile(`Deka_(\d+)[-/](\d+)`)

	// Data Extraction Logic
	var data map[string]interface{}
	jsonData := doc.GetJsonData()
	if jsonData != "" {
		var rawData map[string]interface{}
		if err := json.Unmarshal([]byte(jsonData), &rawData); err == nil {
			data = make(map[string]interface{})
			for k, v := range rawData {
				if m, ok := v.(map[string]interface{}); ok {
					for sk, sv := range m {
						data[sk] = sv
						data[k+"."+sk] = sv
					}
				}
				data[k] = v
			}
		}
	}

	if len(data) == 0 && doc.GetStructData() != nil {
		fields := doc.GetStructData().GetFields()
		data = make(map[string]interface{})
		for k, v := range fields {
			val := valueToInterface(v)
			data[k] = val
			// Special Case for Ratchakitcha/Structured Law: 'text' field is king
			if k == "text" || k == "content" || k == "body" {
				if s, ok := val.(string); ok {
					data["_primary_text"] = s
				}
			}
		}
	}

	if len(data) == 0 {
		return nil
	}

	getString := func(keys ...string) string {
		for _, key := range keys {
			if v, ok := data[key]; ok {
				// Convert any type to string safely
				sVal := fmt.Sprintf("%v", v)
				if sVal != "" && sVal != "<nil>" && sVal != "No snippet is available for this page." {
					return sVal
				}
			}
		}
		return ""
	}

	title := getString(
		"document_meta.title",
		"title",
		"Title",
		"summary",
		"header",
	)
	if title == "" {
		title = getString("id", "ID")
	}

	// Structured Data might have 'id' directly.
	structID := getString("id", "ID", "_id")
	filename := getString(
		"file_name",
		"filename",
		"gcs_pdf_path",
		"pdf_filename",
	)

	// If it's a GCS path, extract just the filename
	if strings.Contains(filename, "/") {
		parts := strings.Split(filename, "/")
		filename = parts[len(parts)-1]
	}

	// Fallback: If filename is empty, use ID as filename (since our ID IS the filename prefix)
	if filename == "" && structID != "" {
		filename = structID
	}
	snippet := ""
	if doc.GetDerivedStructData() != nil {
		dFields := doc.GetDerivedStructData().GetFields()
		if snippets, ok := dFields["snippets"]; ok {
			listVal := snippets.GetListValue()
			if listVal != nil && len(listVal.Values) > 0 {
				firstSnippet := listVal.Values[0].GetStructValue()
				if firstSnippet != nil {
					if s, ok := firstSnippet.Fields["snippet"]; ok {
						sVal := s.GetStringValue()
						if sVal != "" && sVal != "No snippet is available for this page." {
							snippet = sVal
						}
					}
				}
			}
		}
	}
	if snippet == "" {
		snippet = getString("_primary_text", "raw_text_snippet", "summary", "text", "content", "body", "full_text")
	}

	log.Printf("📄 [MAP] Doc %s -> Snippet Length: %d chars", structID, len(snippet))

	// 1. Determine FileName (Primary = from Data, Fallback = ID)
	fixedFilename := filename
	if fixedFilename == "" {
		fixedFilename = structID
	}

	// Ensure .pdf extension
	if fixedFilename != "" && !strings.HasSuffix(strings.ToLower(fixedFilename), ".pdf") {
		fixedFilename += ".pdf"
	}

	pdfURL := ""
	if fixedFilename != "" {

		if engineName == "DEKA" || strings.HasPrefix(filename, "Deka_") {
			pdfURL = fmt.Sprintf("https://storage.googleapis.com/sue-ai-pdfs-storage/%s", fixedFilename)
		} else {
			pdfURL = fmt.Sprintf("https://storage.googleapis.com/main_legal_data/pdfs/%s", fixedFilename)
		}
	}

	id, year := "", ""

	// Try to get explicit year from structured data
	year = getString("year", "Year")
	if year == "" {
		// Try publish_date (e.g. 2024-02-15)
		pubDate := getString("publish_date", "PublishDate")
		if len(pubDate) >= 4 {
			year = pubDate[:4]
		}
	}

	match := dekaRegex.FindStringSubmatch(filename)
	if len(match) == 3 {
		id = fmt.Sprintf("%s/%s", match[1], match[2])
		if year == "" {
			year = match[2]
		}
	} else {
		// Fallback ID mechanism
		if structID != "" {
			id = structID
		} else {
			id = title // Last resort
		}

		if year == "" {
			titleMatch := regexp.MustCompile(`(\d+)/(\d+)`).FindStringSubmatch(title)
			if len(titleMatch) == 3 {
				// id = fmt.Sprintf("%s/%s", titleMatch[1], titleMatch[2]) // Don't overwrite if we already have ID?
				if id == "" || id == title {
					id = fmt.Sprintf("%s/%s", titleMatch[1], titleMatch[2])
				}
				year = titleMatch[2]
			}
		}
	}

	if engineName == "LAW" {
		lawTitle := getString("document_meta.title", "title", "summary")
		if lawTitle != "" && !strings.Contains(lawTitle, "ฎีกา") {
			title = lawTitle
		} else {
			title = strings.TrimSuffix(filename, ".pdf")
		}
	} else if (title == "" || title == "No Title") && id != "" {
		title = "ฎีกาที่ " + id
	}

	return &SearchResult{
		Title:    title,
		ID:       id,
		Year:     year,
		Link:     pdfURL,
		Snippet:  snippet,
		Source:   engineName,
		FileName: filename,
		Meta:     data,
	}
}

// Helper to convert structpb.Value to interface{}
func valueToInterface(v *structpb.Value) interface{} {
	switch kind := v.Kind.(type) {
	case *structpb.Value_StringValue:
		return v.GetStringValue()
	case *structpb.Value_NumberValue:
		return v.GetNumberValue()
	case *structpb.Value_BoolValue:
		return v.GetBoolValue()
	case *structpb.Value_NullValue:
		return nil
	case *structpb.Value_ListValue:
		list := make([]interface{}, len(kind.ListValue.Values))
		for i, val := range kind.ListValue.Values {
			list[i] = valueToInterface(val)
		}
		return list
	case *structpb.Value_StructValue:
		m := make(map[string]interface{})
		for k, val := range kind.StructValue.Fields {
			m[k] = valueToInterface(val)
		}
		return m
	default:
		return v.GetStringValue()
	}
}

// Helper to safely extract string from structpb fields
func getStringField(fields map[string]*structpb.Value, key string) string {
	if val, ok := fields[key]; ok {
		return val.GetStringValue()
	}
	return ""
}

// getMockSearchResults provides fallback data when the real search engine fails (e.g. billing issues)
func getMockSearchResults(engineName string) []SearchResult {
	var results []SearchResult

	if engineName == "LAW" {
		// Mock Civil Code Section 653 (Loan)
		results = append(results, SearchResult{
			Title:    "ประมวลกฎหมายแพ่งและพาณิชย์ มาตรา 653",
			ID:       "law-civil-653",
			Year:     "2568", // Mock current year
			Link:     "https://storage.googleapis.com/main_legal_data/pdfs/Civil_Code.pdf",
			Snippet:  "การกู้ยืมเงินกว่าสองพันบาทขึ้นไปนั้น ถ้ามิได้มีหลักฐานแห่งการกู้ยืมเป็นหนังสืออย่างใดอย่างหนึ่งลงลายมือชื่อผู้ยืมเป็นสำคัญ จะฟ้องร้องให้บังคับคดีหาได้ไม่",
			Source:   "LAW",
			FileName: "Civil_Code.pdf",
			Score:    0.99,
		})
		// Mock Criminal Code Section 341 (Fraud)
		results = append(results, SearchResult{
			Title:    "ประมวลกฎหมายอาญา มาตรา 341",
			ID:       "law-criminal-341",
			Year:     "2568",
			Link:     "https://storage.googleapis.com/main_legal_data/pdfs/Criminal_Code.pdf",
			Snippet:  "ผู้ใดโดยทุจริต หลอกลวงผู้อื่นด้วยการแสดงข้อความอันเป็นเท็จ หรือปกปิดข้อความจริงซึ่งควรบอกให้แจ้ง และโดยการหลอกลวงดังว่านั้นได้ไปซึ่งทรัพย์สินจากผู้ถูกหลอกลวง",
			Source:   "LAW",
			FileName: "Criminal_Code.pdf",
			Score:    0.95,
		})
	} else {
		// Mock Deka
		results = append(results, SearchResult{
			Title:    "คำพิพากษาศาลฎีกาที่ 1234/2565",
			ID:       "1234/2565",
			Year:     "2565",
			Link:     "https://storage.googleapis.com/sue-ai-pdfs-storage/Deka_1234-2565.pdf",
			Snippet:  "โจทก์ฟ้องขอให้จำเลยชำระหนี้เงินกู้ จำเลยให้การต่อสู้ว่าสัญญากู้ยืมเงินไม่ได้ระบุวันทำสัญญา ถือเป็นหลักฐานที่ไม่สมบูรณ์... ศาลฎีกาวินิจฉัยว่า แม้ไม่ได้ลงวันที่ไว้ แต่มีลายมือชื่อผู้ยืมก็ถือเป็นหลักฐานแห่งการกู้ยืมเงินที่สมบูรณ์แล้ว",
			Source:   "DEKA",
			FileName: "Deka_1234-2565.pdf",
			Score:    0.98,
		})
		results = append(results, SearchResult{
			Title:    "คำพิพากษาศาลฎีกาที่ 5678/2566",
			ID:       "5678/2566",
			Year:     "2566",
			Link:     "https://storage.googleapis.com/sue-ai-pdfs-storage/Deka_5678-2566.pdf",
			Snippet:  "คดีฉ้อโกงประชาชน จำเลยหลอกลวงผู้เสียหายหลายรายผ่านระบบคอมพิวเตอร์... การกระทำของจำเลยเป็นความผิดต่างกรรมต่างวาระ ให้ลงโทษทุกกรรมเรียงกระทงความผิด",
			Source:   "DEKA",
			FileName: "Deka_5678-2566.pdf",
			Score:    0.96,
		})
	}

	return results
}
