#!/bin/bash

# ==========================================
# 🚀 Sue.AI Deployment Script (Google Cloud Run)
# ==========================================

# 1. Configuration
PROJECT_ID="gen-lang-client-0464468580"
REGION="asia-southeast1"
BACKEND_SERVICE_NAME="sue-ai-backend-go" # Correct Legacy Name
FRONTEND_SERVICE_NAME="sue-ai-frontend"

echo "🔥 Starting Deployment for Project: $PROJECT_ID"
echo "🌍 Region: $REGION"

# 2. Deploy Backend
echo "\n--------------------------------------"
echo "🛠️  Building & Deploying BACKEND..."
echo "--------------------------------------"

# Load Environment Variables from Backend .env
if [ -f "src/backend-go/.env" ]; then
  export $(grep -v '^#' src/backend-go/.env | xargs)
  echo "✅ Loaded Environment Variables from src/backend-go/.env"
else
  echo "⚠️  .env file not found! Please ensure variables are set."
fi

cd src/backend-go

# Deploy Backend
# Build & Push to GCR
gcloud builds submit --tag gcr.io/$PROJECT_ID/$BACKEND_SERVICE_NAME --project $PROJECT_ID .

# Deploy to Cloud Run (Using Env Vars from .env)
gcloud run deploy $BACKEND_SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$BACKEND_SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars GEMINI_API_KEY="$GEMINI_API_KEY",PROJECT_ID="$PROJECT_ID",ENGINE_ID_DEKA="$ENGINE_ID_DEKA",ENGINE_ID_LAW="$ENGINE_ID_LAW",GOOGLE_APPLICATION_CREDENTIALS="service-account.json"
  
# Get Backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE_NAME --platform managed --region $REGION --project $PROJECT_ID --format 'value(status.url)')
echo "✅ Backend Deployed at: $BACKEND_URL"

echo "\n--------------------------------------"
echo "⚠️  Frontend Deployment Skipped (Vercel Managed)"
echo "--------------------------------------"
echo "Please update your Vercel project with the new Backend URL:"
echo "NEXT_PUBLIC_API_URL=$BACKEND_URL"

echo "\n=========================================="
echo "🚀 BACKEND DEPLOYMENT COMPLETE!"
echo "Backend URL: $BACKEND_URL"
echo "=========================================="
