package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

type Config struct {
	Port            string
	ProjectID       string
	DataStoreIDDeka string
	DataStoreIDLaw  string
	EngineIDDeka    string
	EngineIDLaw     string
	GeminiAPIKey    string
	CredentialsFile string
}

// LoadConfig reads configuration from environment variables or .env file
func LoadConfig() *Config {
	// Attempt to load .env file from common locations based on execution root
	_ = godotenv.Load()                      // ./.env
	_ = godotenv.Load("../../.env")          // from cmd/server/ (Standard Go layout)
	_ = godotenv.Load("../.env")             // from cmd/
	_ = godotenv.Load("src/backend-go/.env") // from Project Root
	_ = godotenv.Load(".env")                // from src/backend-go/

	key := getEnv("GEMINI_API_KEY", "")
	// Sanitize: strip double quotes if any (common in some .env formats)
	if len(key) > 2 && key[0] == '"' && key[len(key)-1] == '"' {
		key = key[1 : len(key)-1]
	}

	cfg := &Config{
		Port:            getEnv("PORT", "8080"),
		ProjectID:       getEnv("GCP_PROJECT_ID", ""),
		DataStoreIDDeka: getEnv("DATA_STORE_ID_DEKA", ""),
		DataStoreIDLaw:  getEnv("DATA_STORE_ID_LAW", ""),
		EngineIDDeka:    getEnv("ENGINE_ID_DEKA", "sue-ai-search_1768730959752"),
		EngineIDLaw:     getEnv("ENGINE_ID_LAW", "sue-ai-legal-unified-v3"),
		GeminiAPIKey:    key,
		CredentialsFile: getEnv("GOOGLE_APPLICATION_CREDENTIALS", ""),
	}

	// Debug: Log loaded config values
	log.Printf("📋 Config Loaded:")
	log.Printf("   ProjectID: %s", cfg.ProjectID)
	log.Printf("   EngineIDDeka: %s", cfg.EngineIDDeka)
	log.Printf("   EngineIDLaw: %s", cfg.EngineIDLaw)
	log.Printf("   DataStoreIDDeka: %s", cfg.DataStoreIDDeka)
	log.Printf("   DataStoreIDLaw: %s", cfg.DataStoreIDLaw)

	return cfg
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return fallback
}
