#!/bin/bash
export PROJECT_ID="gen-lang-client-0464468580"
export REGION="asia-southeast1"
export APP_NAME="sue-ai-frontend"
export REPO_NAME="sue-ai-repo" # Assume we have a repo, or use gcr.io

# Enable Artifact Registry API
gcloud services enable artifactregistry.googleapis.com

# Create Repo if not exists (Standard Docker Repo)
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --project=$PROJECT_ID \
    --description="Sue AI Docker Repository" || true

# Helper to configure docker auth (Quiet mode)
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Build & Push
echo "🚀 Building Frontend..."
cd src/frontend
# Explicitly use project ID in tag
docker build --platform linux/amd64 -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${APP_NAME}:latest .

echo "📤 Pushing to Artifact Registry..."
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${APP_NAME}:latest

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${APP_NAME} \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${APP_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --allow-unauthenticated \
    --port 3000 \
    --set-env-vars NEXT_PUBLIC_API_URL="https://sue-ai-backend-go-289893785097.asia-southeast1.run.app" 
    # NOTE: We need the REAL Backend URL here! 
    # I'll use a placeholder or verify the backend URL first.

echo "✅ Deployment Complete!"
