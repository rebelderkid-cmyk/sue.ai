package rag

import (
	"context"
	"fmt"

	"sue-ai-backend/internal/config"

	discoveryengine "cloud.google.com/go/discoveryengine/apiv1"
	"github.com/google/generative-ai-go/genai"
	"google.golang.org/api/option"
)

type RAGService struct {
	SearchClient *discoveryengine.SearchClient
	GenModel     *genai.GenerativeModel
	GenClient    *genai.Client // Exposed to share with Agent Logic
	Config       *config.Config
}

func NewRAGService(ctx context.Context, cfg *config.Config) (*RAGService, error) {
	// 1. Init Vertex AI Search Client
	// IF running on Cloud Run with Default Service Account, NewSearchClient() works automatically via ADC.
	var searchClient *discoveryengine.SearchClient
	var err error

	if cfg.CredentialsFile != "" {
		searchClient, err = discoveryengine.NewSearchClient(ctx, option.WithCredentialsFile(cfg.CredentialsFile))
	} else {
		// Use ADC (Application Default Credentials) - Ideal for Cloud Run
		searchClient, err = discoveryengine.NewSearchClient(ctx)
	}

	if err != nil {
		return nil, fmt.Errorf("failed to create discovery engine client: %w", err)
	}

	// 2. Init Gemini Client
	var genClient *genai.Client
	if cfg.GeminiAPIKey != "" {
		genClient, err = genai.NewClient(ctx, option.WithAPIKey(cfg.GeminiAPIKey))
	} else {
		return nil, fmt.Errorf("GEMINI_API_KEY is missing")
	}

	if err != nil {
		return nil, fmt.Errorf("failed to create custom generative ai client: %w", err)
	}

	// Configure Model
	model := genClient.GenerativeModel("gemini-2.5-flash-preview-09-2025") // User Requested High-End Model 🚀
	model.SetTemperature(0.4)                                              // Optimized for consistency

	return &RAGService{
		SearchClient: searchClient,
		GenModel:     model,
		GenClient:    genClient, // Store Client for reuse
		Config:       cfg,
	}, nil
}

func (s *RAGService) Close() {
	s.SearchClient.Close()
	// GenClient doesn't have a strict Close() in some versions, but good practice if available
}
