package memory

import (
	"sync"
	"time"

	"sue-ai-backend/internal/rag"
)

// SessionData holds the state for a single conversation
type SessionData struct {
	LastSearchResults []rag.SearchResult
	LastUpdatedAt     time.Time
}

// MemoryStore is a thread-safe in-memory cache
type MemoryStore struct {
	sessions map[string]*SessionData
	mu       sync.RWMutex
}

// Global Memory Instance
var globalMemory *MemoryStore
var once sync.Once

// GetMemory returns the singleton memory store
func GetMemory() *MemoryStore {
	once.Do(func() {
		globalMemory = &MemoryStore{
			sessions: make(map[string]*SessionData),
		}
		// Start cleanup routine
		go globalMemory.cleanupRoutine()
	})
	return globalMemory
}

// SaveContext stores the search results for a conversation
func (m *MemoryStore) SaveContext(conversationID string, results []rag.SearchResult) {
	m.mu.Lock()
	defer m.mu.Unlock()

	// If no ID provided (e.g. first separate message without ID), skip or use temp?
	// The frontend sends conversation_id in the last history message usually.
	if conversationID == "" {
		return
	}

	m.sessions[conversationID] = &SessionData{
		LastSearchResults: results,
		LastUpdatedAt:     time.Now(),
	}
}

// GetContext retrieves the last search results
func (m *MemoryStore) GetContext(conversationID string) []rag.SearchResult {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if data, ok := m.sessions[conversationID]; ok {
		return data.LastSearchResults
	}
	return nil
}

// Cleanup routine to remove old sessions (e.g. > 1 hour)
func (m *MemoryStore) cleanupRoutine() {
	for {
		time.Sleep(10 * time.Minute)
		m.mu.Lock()
		for id, data := range m.sessions {
			if time.Since(data.LastUpdatedAt) > 1*time.Hour {
				delete(m.sessions, id)
			}
		}
		m.mu.Unlock()
	}
}
