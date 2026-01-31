package main

import (
	"context"
	"fmt"
	"log"
	"os"

	discoveryengine "cloud.google.com/go/discoveryengine/apiv1"
	"cloud.google.com/go/discoveryengine/apiv1/discoveryenginepb"
	"google.golang.org/api/iterator"
	"google.golang.org/api/option"
)

func main() {
	ctx := context.Background()

	// Read config from env
	projectID := os.Getenv("PROJECT_ID")
	if projectID == "" {
		projectID = "gen-lang-client-0464468580"
	}

	dekaEngineID := os.Getenv("ENGINE_ID_DEKA")
	if dekaEngineID == "" {
		dekaEngineID = "deka_1768730204117"
	}

	lawEngineID := os.Getenv("ENGINE_ID_LAW")
	if lawEngineID == "" {
		lawEngineID = "main-legal_1768906525188"
	}

	// Create search client
	searchClient, err := discoveryengine.NewSearchClient(ctx, option.WithEndpoint("discoveryengine.googleapis.com:443"))
	if err != nil {
		log.Fatalf("Failed to create search client: %v", err)
	}
	defer searchClient.Close()

	// Test queries
	testQueries := []string{
		"*", // Wildcard - should return everything
		"กฎหมาย",
		"ฎีกา",
		"มาตรา",
		"ลักทรัพย์",
	}

	engines := map[string]string{
		"DEKA": dekaEngineID,
		"LAW":  lawEngineID,
	}

	for engineName, engineID := range engines {
		fmt.Printf("\n\n========== Testing %s Engine (ID: %s) ==========\n", engineName, engineID)

		for _, query := range testQueries {
			fmt.Printf("\n🔍 Query: '%s'\n", query)

			servingConfig := fmt.Sprintf(
				"projects/%s/locations/global/collections/default_collection/engines/%s/servingConfigs/default_search",
				projectID, engineID,
			)

			req := &discoveryenginepb.SearchRequest{
				ServingConfig: servingConfig,
				Query:         query,
				PageSize:      5,
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
				fmt.Printf("   📄 [%d] ID: %s\n", count, doc.Id)

				// Print available keys
				if doc.GetStructData() != nil {
					keys := []string{}
					for k := range doc.GetStructData().GetFields() {
						keys = append(keys, k)
					}
					fmt.Printf("       StructData keys: %v\n", keys)
				}

				if doc.GetDerivedStructData() != nil {
					keys := []string{}
					for k := range doc.GetDerivedStructData().GetFields() {
						keys = append(keys, k)
					}
					fmt.Printf("       DerivedStructData keys: %v\n", keys)
				}

				if count >= 3 {
					fmt.Printf("   ... (truncated, showing first 3)\n")
					break
				}
			}

			if count == 0 {
				fmt.Printf("   ⚠️ No results found!\n")
			} else {
				fmt.Printf("   ✅ Found %d+ results\n", count)
			}
		}
	}

	fmt.Println("\n\n========== Test Complete ==========")
}
