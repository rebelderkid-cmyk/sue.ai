package main

import (
	"context"
	"fmt"
	"log"

	discoveryengine "cloud.google.com/go/discoveryengine/apiv1"
	"cloud.google.com/go/discoveryengine/apiv1/discoveryenginepb"
	"google.golang.org/api/iterator"
	"google.golang.org/api/option"
)

func main() {
	ctx := context.Background()

	projectID := "gen-lang-client-0464468580"
	lawEngineID := "main-legal-search_1768906502953"

	searchClient, err := discoveryengine.NewSearchClient(ctx, option.WithEndpoint("discoveryengine.googleapis.com:443"))
	if err != nil {
		log.Fatalf("Failed: %v", err)
	}
	defer searchClient.Close()

	// Test queries for various law types
	queries := []string{
		"พ.ร.บ.",
		"ประมวลกฎหมายอาญา",
		"ประมวลกฎหมายแพ่งและพาณิชย์",
		"พ.ร.บ.คุ้มครองผู้บริโภค",
		"พ.ร.บ.คอมพิวเตอร์",
		"มาตรา 112",
		"กฎหมายแรงงาน",
	}

	fmt.Println("========== Testing LAW Engine ==========")
	fmt.Printf("Engine ID: %s\n\n", lawEngineID)

	for _, query := range queries {
		fmt.Printf("🔍 Query: '%s'\n", query)

		servingConfig := fmt.Sprintf(
			"projects/%s/locations/global/collections/default_collection/engines/%s/servingConfigs/default_search",
			projectID, lawEngineID,
		)

		req := &discoveryenginepb.SearchRequest{
			ServingConfig: servingConfig,
			Query:         query,
			PageSize:      3,
		}

		it := searchClient.Search(ctx, req)

		count := 0
		for {
			resp, err := it.Next()
			if err == iterator.Done {
				break
			}
			if err != nil {
				fmt.Printf("   ❌ Error: %v\n", err)
				break
			}

			doc := resp.Document
			if doc == nil {
				continue
			}

			count++

			// Extract title
			title := doc.Id
			if doc.GetStructData() != nil {
				if t, ok := doc.GetStructData().GetFields()["title"]; ok {
					title = t.GetStringValue()
				}
				if t, ok := doc.GetStructData().GetFields()["document_meta.title"]; ok && t.GetStringValue() != "" {
					title = t.GetStringValue()
				}
			}

			// Extract doc_type
			docType := "-"
			if doc.GetStructData() != nil {
				if t, ok := doc.GetStructData().GetFields()["doc_type"]; ok {
					docType = t.GetStringValue()
				}
			}

			// Extract snippet
			snippet := ""
			if doc.GetStructData() != nil {
				if s, ok := doc.GetStructData().GetFields()["raw_text_snippet"]; ok {
					snippet = s.GetStringValue()
					if len(snippet) > 150 {
						snippet = snippet[:150] + "..."
					}
				}
			}

			fmt.Printf("   📄 [%d] %s\n", count, title)
			fmt.Printf("       Type: %s\n", docType)
			fmt.Printf("       Snippet: %s\n", snippet)
		}

		if count == 0 {
			fmt.Printf("   ⚠️ No results found!\n")
		}
		fmt.Println()
	}
}
