#!/bin/bash

# Load env vars
export $(grep -v '^#' .env | xargs)

# Determine script directory to allow running from anywhere
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../../src/backend"

echo "🚀 Deploying Sue.AI Backend (Serverless) to Google Cloud Run..."
echo "🔹 Project: $GCP_PROJECT_ID"
echo "🔹 Source: $BACKEND_DIR"

gcloud run deploy sue-ai-backend \
  --source "$BACKEND_DIR" \
  --project $GCP_PROJECT_ID \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$GCP_PROJECT_ID,DATA_STORE_ID=$DATA_STORE_ID,GEMINI_API_KEY=$GEMINI_API_KEY

echo "✅ Deployment Command Sent!"
