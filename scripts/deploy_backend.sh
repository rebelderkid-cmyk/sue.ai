#!/bin/bash
# deploy_backend.sh

# 1. Configuration
SERVICE_NAME="sue-ai-backend"
REGION="asia-southeast1" # Singapore
PROJECT_ID="gen-lang-client-0464468580"
SRC_DIR="src/backend"

# 2. Load Environment Variables from .env logic
# We need to explicitly pass these to Cloud Run
if [ -f "$SRC_DIR/.env" ]; then
    export $(cat $SRC_DIR/.env | grep -v '#' | xargs)
    echo "✅ Loaded env vars from $SRC_DIR/.env"
else
    echo "❌ Error: $SRC_DIR/.env not found!"
    exit 1
fi

# Check for Critical Keys
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️ Warning: GEMINI_API_KEY is missing in .env. Deployment might fail or AI won't work."
    # Try to grab it from current shell if exported
fi

echo "🚀 Deploying $SERVICE_NAME to Cloud Run ($REGION)..."
echo "   - Project: $PROJECT_ID"
echo "   - Data Store: $DATA_STORE_ID"

# 3. Submit Build & Deploy
# Using source=. to upload the current directory (src/backend) to Cloud Build
gcloud run deploy $SERVICE_NAME \
    --source "$SRC_DIR" \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --quiet \
    --set-env-vars GCP_PROJECT_ID=$PROJECT_ID \
    --set-env-vars DATA_STORE_ID_DEKA=$DATA_STORE_ID_DEKA \
    --set-env-vars DATA_STORE_ID_LAW=$DATA_STORE_ID_LAW \
    --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY \
    --set-env-vars LOCATION=global

echo "🎉 Deployment Command Sent!"
