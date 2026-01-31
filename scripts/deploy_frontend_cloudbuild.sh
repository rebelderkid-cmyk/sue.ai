#!/bin/bash
PROJECT_ID="gen-lang-client-0464468580"
REGION="asia-southeast1"
APP_NAME="sue-ai-frontend"
REPO_NAME="sue-ai-repo" 
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${APP_NAME}:latest"

if [ -z "$1" ]; then
  echo "Usage: $0 <BACKEND_URL>"
  exit 1
fi

BACKEND_URL=$1
echo "🚀 Deploying Frontend with Backend URL: $BACKEND_URL"

# Enable Artifact Registry (idempotent)
gcloud services enable artifactregistry.googleapis.com

# Create Repo if not exists (Standard Docker Repo)
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --project=$PROJECT_ID \
    --description="Sue AI Docker Repository" || true

cd src/frontend

echo "🔨 Building with Cloud Build..."
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_NEXT_PUBLIC_API_URL="$BACKEND_URL",_IMAGE_NAME="$IMAGE_NAME" \
  --project="$PROJECT_ID" .

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${APP_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --allow-unauthenticated \
    --port 3000 \

echo "✅ Frontend Deployment Complete!"
