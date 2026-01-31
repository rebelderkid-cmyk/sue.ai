package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/google/generative-ai-go/genai"
	"google.golang.org/api/iterator"
	"google.golang.org/api/option"
)

func main() {
	ctx := context.Background()
	apiKey := os.Getenv("GEMINI_API_KEY")
	if apiKey == "" {
		// Try to read from .env manually or fallback
		apiKey = "AIzaSyB6t5VFdMSX-rMMVQ7rmvpe_dxqNHIIamA" // From previous view_file of .env
	}

	client, err := genai.NewClient(ctx, option.WithAPIKey(apiKey))
	if err != nil {
		log.Fatal(err)
	}
	defer client.Close()

	iter := client.ListModels(ctx)
	fmt.Println("Available Gemini Models:")
	for {
		m, err := iter.Next()
		if err == iterator.Done {
			break
		}
		if err != nil {
			log.Fatal(err)
		}
		// Filter only generateContent supported models
		if supportsGenerateContent(m) {
			fmt.Printf("- %s (%s) - version: %s\n", m.Name, m.DisplayName, m.Version)
		}
	}
}

func supportsGenerateContent(m *genai.ModelInfo) bool {
	for _, method := range m.SupportedGenerationMethods {
		if method == "generateContent" {
			return true
		}
	}
	return false
}
