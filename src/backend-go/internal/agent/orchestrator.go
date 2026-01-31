package agent

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strings"
	"unicode/utf8"

	"github.com/google/generative-ai-go/genai"
)

// IntentResult defines the decision made by the AI
type IntentResult struct {
	Action string `json:"action"` // "SEARCH" or "ANSWER"
	Reason string `json:"reason"`
}

// IntentAnalyzer handles the classification logic
type IntentAnalyzer struct {
	Model *genai.GenerativeModel
}

func NewIntentAnalyzer(client *genai.Client) *IntentAnalyzer {
	// Use a lightweight model for this task (Flash is perfect)
	// Updated to the working V3 model
	model := client.GenerativeModel("gemini-3-flash-preview")
	model.SetTemperature(0.1) // Low temperature for deterministic results
	model.ResponseMIMEType = "application/json"
	return &IntentAnalyzer{Model: model}
}

// Classify determines if the user's query needs a new search or can be answered from history
func (a *IntentAnalyzer) Classify(ctx context.Context, history []map[string]string, question string) (IntentResult, error) {
	// If no history, ALWAYS search
	if len(history) == 0 {
		return IntentResult{Action: "SEARCH", Reason: "No history context"}, nil
	}

	// Force SEARCH for strong keywords (Override AI)
	strongKeywords := []string{"วิเคราะห์", "ประเมิน", "ฎีกา", "มาตรา", "กฎหมาย", "คืออะไร", "ช่วยค้น", "สรุป", "analyze", "find", "search", "law"}
	for _, kw := range strongKeywords {
		if strings.Contains(strings.ToLower(question), kw) {
			// But wait! If it's "analyze FURTHER" or "explain the SECTION", it might be ANSWER.
			// Let's rely on AI but give it a strong hint.
			// Actually, let's force search if it looks like a stand-alone query.
			// For now, let the improved Prompt handle it, or we risk breaking follow-ups like "Does section 123 apply here?"
		}
	}

	// Sanitize input to prevent UTF-8 errors
	cleanHistory := sanitizeUTF8(formatHistory(history))
	cleanQuestion := sanitizeUTF8(question)

	prompt := fmt.Sprintf(`You are the "Brain" of a Legal AI Assistant.
Your job is to decide the next action based on the Conversation History and the User's Latest Question.

ACTIONS:
- "SEARCH": 
    - Determining a NEW case / topic / question.
    - User asks to "Analyze", "Find", "Search", "Summarize law", "Check Deka".
    - Any query containing specific Section numbers (e.g. "Section 420") or Case IDs (e.g. "23/2560") that were NOT just discussed.
    - If the user asks "What is...", "How to...", "Can I..." about legal topics.
- "ANSWER": 
    - Only for conversational follow-ups (e.g. "Explain more", "What does that mean?", "How about the penalty?", "Does it apply to me?").
    - Referring to "the previous case", "this section", "that law".

When in doubt, choose "SEARCH" to ensure latest data is retrieved.

Conversation History:
%s

User Question:
"%s"

Return JSON only: { "action": "SEARCH" | "ANSWER", "reason": "reasoning in english" }`, cleanHistory, cleanQuestion)

	resp, err := a.Model.GenerateContent(ctx, genai.Text(prompt))
	if err != nil {
		return IntentResult{Action: "SEARCH", Reason: "Analysis Failed"}, err
	}

	if len(resp.Candidates) == 0 || len(resp.Candidates[0].Content.Parts) == 0 {
		return IntentResult{Action: "SEARCH", Reason: "Empty Response"}, fmt.Errorf("empty response")
	}

	var result IntentResult
	for _, part := range resp.Candidates[0].Content.Parts {
		if txt, ok := part.(genai.Text); ok {
			rawJSON := string(txt)
			// Clean Markdown code blocks if present
			rawJSON = strings.TrimSpace(rawJSON)
			if strings.HasPrefix(rawJSON, "```json") {
				rawJSON = strings.TrimPrefix(rawJSON, "```json")
				rawJSON = strings.TrimSuffix(rawJSON, "```")
			} else if strings.HasPrefix(rawJSON, "```") {
				rawJSON = strings.TrimPrefix(rawJSON, "```")
				rawJSON = strings.TrimSuffix(rawJSON, "```")
			}
			rawJSON = strings.TrimSpace(rawJSON)

			if err := json.Unmarshal([]byte(rawJSON), &result); err == nil {
				return result, nil
			} else {
				log.Printf("Intent parsing error: %v | Raw: %s", err, txt)
			}
		}
	}

	// Fallback
	return IntentResult{Action: "SEARCH", Reason: "Parsing Fallback"}, nil
}

func formatHistory(hist []map[string]string) string {
	out := ""
	// Take last 4 turns for context window efficiency
	start := 0
	if len(hist) > 4 {
		start = len(hist) - 4
	}
	for _, h := range hist[start:] {
		role := "User"
		if h["role"] == "assistant" || h["role"] == "model" {
			role = "AI"
		}
		// Truncate long content
		content := h["content"]
		if len(content) > 200 {
			content = content[:200] + "..."
		}
		out += fmt.Sprintf("%s: %s\n", role, content)
	}
	return out
}

// sanitizeUTF8 removes invalid UTF-8 sequences from a string
func sanitizeUTF8(s string) string {
	if utf8.ValidString(s) {
		return s
	}

	// Build a new string with only valid UTF-8 runes
	var builder strings.Builder
	builder.Grow(len(s))

	for i := 0; i < len(s); {
		r, size := utf8.DecodeRuneInString(s[i:])
		if r == utf8.RuneError && size == 1 {
			// Invalid byte, skip it
			i++
			continue
		}
		builder.WriteRune(r)
		i += size
	}

	return builder.String()
}
