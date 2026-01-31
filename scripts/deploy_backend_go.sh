#!/bin/bash

# Configuration
PROJECT_ID="gen-lang-client-0464468580"
REGION="asia-southeast1"
SERVICE_NAME="sue-ai-backend-go" # New Service Name to avoid conflict with Python temporarily
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Helper colors
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Preparing to deploy Sue.AI Backend (Go Version)...${NC}"

# Navigate to Go Source Directory
cd src/backend-go || exit

# Load .env (from original backend location if needed, or assume Env Vars are set in Cloud Run)
# For local build context, we might need value of ENV vars.
# Actually, gcloud run deploy --set-env-vars needs actual values.
# Let's extract them from the python .env file for convenience.
# Load .env (from local directory)
if [ -f ".env" ]; then
    echo "✅ Loaded env vars from .env"
    export $(grep -v '^#' .env | xargs)
elif [ -f "../backend/.env" ]; then
    echo "⚠️ .env not found in src/backend-go, trying src/backend/.env"
    export $(grep -v '^#' ../backend/.env | xargs)
else
    echo "❌ No .env file found! Deployment might fail if env vars are missing."
fi

echo -e "${GREEN}🔨 Building and Pushing Container to Google Container Registry...${NC}"

# One-step Build & Deploy using Cloud Build (No local Docker needed)
# One-step Build & Deploy (Direct Build, ignoring cloudbuild.yaml to avoid substitution errors)
gcloud builds submit --tag "${IMAGE_NAME}" --project "${PROJECT_ID}" .

echo -e "${GREEN}🚀 Deploying to Cloud Run...${NC}"

gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_NAME}" \
  --platform managed \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars GCP_PROJECT_ID="${PROJECT_ID}" \
  --set-env-vars DATA_STORE_ID_DEKA="${DATA_STORE_ID_DEKA}" \
  --set-env-vars DATA_STORE_ID_LAW="${DATA_STORE_ID_LAW}" \
  --set-env-vars ENGINE_ID_DEKA="${ENGINE_ID_DEKA}" \
  --set-env-vars ENGINE_ID_LAW="${ENGINE_ID_LAW}" \
  --set-env-vars GEMINI_API_KEY="${GEMINI_API_KEY}"

echo -e "${GREEN}🎉 Deployment Complete! Service: ${SERVICE_NAME}${NC}"
