package main

import (
	"context"
	"log"

	"github.com/gin-gonic/gin"
	"sue-ai-backend/internal/api"
	"sue-ai-backend/internal/config"
	"sue-ai-backend/internal/rag"
)

func main() {
	// 1. Load Config
	cfg := config.LoadConfig()

	// 2. Initialize RAG Service (Vertex AI + Gemini)
	ragService, err := rag.NewRAGService(context.Background(), cfg)
	if err != nil {
		log.Fatalf("❌ Failed to init RAG Service: %v", err)
	}
	defer ragService.Close()

	// 3. Initialize Handler
	h := api.NewHandler(ragService)

	// 4. Setup Router
	r := gin.Default()
	
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status": "ok", 
			"mode": "god_mode_go_lang",
			"backend": "go-gin",
		})
	})

	// Register API Routes
	api.RegisterRoutes(r, h)

	// 5. Run Server
	log.Printf("🚀 Sue.AI Backend (Go) starting on port %s", cfg.Port)
	if err := r.Run(":" + cfg.Port); err != nil {
		log.Fatalf("❌ Failed to start server: %v", err)
	}
}
