package rag

import (
	"context"
	"fmt"
	"log"
	"regexp"
	"sort"
	"strconv"
	"strings"

	// Discovery Engine
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
	Title    string                 `json:"title"`
	Link     string                 `json:"pdf_url"`
	Snippet  string                 `json:"snippet"`
	Source   string                 `json:"source"`
	FileName string                 `json:"filename"`
	Content  string                 `json:"content"`
	ID       string                 `json:"id"`
	Year     string                 `json:"year"`
	Meta     map[string]interface{} `json:"meta"`
	Raw      interface{}            `json:"raw,omitempty"`
	Score    float64                `json:"score"`
}

// Search performs a standard Vertex AI Search and applies Re-ranking with Transparent Logging
func (s *RAGService) Search(ctx context.Context, queries OptimizedQueries, filters map[string]interface{}) ([]SearchResult, error) {
	engineID := s.Config.EngineIDDeka
	if strings.Contains(engineID, "/") {
		parts := strings.Split(engineID, "/")
		engineID = parts[len(parts)-1]
	}

	servingConfig := fmt.Sprintf(
		"projects/%s/locations/global/collections/default_collection/engines/%s/servingConfigs/default_config",
		s.Config.ProjectID, engineID,
	)

	// Step 1: Extract core keywords from optimized query
	keywords := strings.Fields(queries.DekaQuery)
	var cleanKeywords []string
	for _, k := range keywords {
		k = strings.Trim(k, " ,.()\"'")
		if len([]rune(k)) >= 2 {
			cleanKeywords = append(cleanKeywords, strings.ToLower(k))
		}
	}

	log.Printf("🧪 [RE-RANK] Analyzing with keywords: %v", cleanKeywords)

	// Step 2: Fetch large pool
	limit := 100
	req := &discoveryenginepb.SearchRequest{
		ServingConfig: servingConfig,
		Query:         queries.DekaQuery,
		PageSize:      int32(limit),
		ContentSearchSpec: &discoveryenginepb.SearchRequest_ContentSearchSpec{
			SnippetSpec: &discoveryenginepb.SearchRequest_ContentSearchSpec_SnippetSpec{
				ReturnSnippet: true,
			},
		},
	}

	it := s.SearchClient.Search(ctx, req)
	var pool []SearchResult
	rank := 0

	for {
		if rank >= limit {
			break
		}
		resp, err := it.Next()
		if err == iterator.Done {
			break
		}
		if err != nil {
			break
		}

		if res := s.mapDocumentToSearchResult(resp.Document, "DEKA"); res != nil {
			// Step 3: Detailed Keyword Comparison
			matches := []string{}
			haystack := strings.ToLower(res.Title + " " + res.Snippet)
			for _, kw := range cleanKeywords {
				if strings.Contains(haystack, kw) {
					matches = append(matches, kw)
				}
			}

			// Step 4: Hybrid Scoring Formula (Visible)
			yearInt, _ := strconv.Atoi(res.Year)
			if yearInt == 0 {
				yearInt = 2400
			} // Fallback

			yearScore := float64(yearInt) * 10000.0
			matchScore := float64(len(matches)) * 1500.0
			rankPenalty := float64(rank)

			res.Score = yearScore + matchScore - rankPenalty

			// Optional: Log every item (internal debug)
			// log.Printf("   - Doc %s: Year=%d (%v), Keywords=%v, Score=%.0f", res.ID, yearInt, res.Year, matches, res.Score)

			pool = append(pool, *res)
			rank++
		}
	}

	// Step 5: Final Sort
	sort.Slice(pool, func(i, j int) bool {
		return pool[i].Score > pool[j].Score
	})

	// Step 6: Visual Report in Logs
	log.Printf("📊 RERANK LEADERBOARD (Top 10):")
	for i := 0; i < 10 && i < len(pool); i++ {
		p := pool[i]
		matchKeywords := []string{}
		haystack := strings.ToLower(p.Title + " " + p.Snippet)
		for _, kw := range cleanKeywords {
			if strings.Contains(haystack, kw) {
				matchKeywords = append(matchKeywords, kw)
			}
		}

		log.Printf("   #%d [%s] Year: %s | Matches: %d %v | TotalScore: %.0f",
			i+1, p.ID, p.Year, len(matchKeywords), matchKeywords, p.Score)
	}

	return pool, nil
}

func (s *RAGService) mapDocumentToSearchResult(doc *discoveryenginepb.Document, engineName string) *SearchResult {
	if doc == nil {
		return nil
	}

	dataMap := make(map[string]interface{})
	if sd := doc.GetStructData(); sd != nil {
		for k, v := range sd.GetFields() {
			dataMap[k] = valueToInterface(v)
		}
	}

	getStr := func(keys ...string) string {
		for _, k := range keys {
			if v, ok := dataMap[k]; ok {
				return fmt.Sprintf("%v", v)
			}
		}
		return ""
	}

	title := getStr("title", "Topic", "Name")
	if title == "" {
		title = doc.Id
	}

	snippet := ""
	if dsd := doc.GetDerivedStructData(); dsd != nil {
		if snips, ok := dsd.GetFields()["snippets"]; ok {
			if lv := snips.GetListValue(); lv != nil {
				for _, v := range lv.GetValues() {
					if sm := v.GetStructValue(); sm != nil {
						if c, ok := sm.GetFields()["snippet"]; ok {
							snippet += c.GetStringValue() + " ... "
						}
					}
				}
			}
		}
	}

	if snippet == "" {
		snippet = getStr("content", "body", "text", "description", "snippet")
		if len(snippet) > 150 {
			runes := []rune(snippet)
			snippet = string(runes[:150]) + "..."
		}
	}

	content := getStr("content", "body", "text", "text_content", "Full_Text", "full_text", "Content")

	year := getStr("year", "Year", "year_deka", "Year_Deka")
	if year == "" {
		re := regexp.MustCompile(`/(25\d{2})`)
		if m := re.FindStringSubmatch(title); len(m) > 1 {
			year = m[1]
		} else if m := re.FindStringSubmatch(doc.Id); len(m) > 1 {
			year = m[1]
		}
	}

	link := getStr("link", "pdf_url", "uri", "url", "Link", "pdf_link")
	if link == "" {
		fname := getStr("filename", "file_name")
		if fname != "" {
			if !strings.HasSuffix(strings.ToLower(fname), ".pdf") {
				fname += ".pdf"
			}
			link = "https://storage.googleapis.com/sue-ai-pdfs-storage/" + fname
		}
	}

	if strings.HasPrefix(link, "gs://") {
		link = strings.Replace(link, "gs://", "https://storage.googleapis.com/", 1)
	}

	return &SearchResult{
		Title:   title,
		Link:    link,
		Snippet: snippet,
		Source:  engineName,
		Content: content,
		ID:      doc.Id,
		Year:    year,
		Meta:    dataMap,
	}
}

func valueToInterface(v *structpb.Value) interface{} {
	if v == nil {
		return nil
	}
	switch kind := v.Kind.(type) {
	case *structpb.Value_NumberValue:
		return kind.NumberValue
	case *structpb.Value_StringValue:
		return kind.StringValue
	case *structpb.Value_BoolValue:
		return kind.BoolValue
	case *structpb.Value_StructValue:
		m := make(map[string]interface{})
		for k, val := range kind.StructValue.GetFields() {
			m[k] = valueToInterface(val)
		}
		return m
	case *structpb.Value_ListValue:
		var l []interface{}
		for _, val := range kind.ListValue.GetValues() {
			l = append(l, valueToInterface(val))
		}
		return l
	default:
		return v.GetStringValue()
	}
}
