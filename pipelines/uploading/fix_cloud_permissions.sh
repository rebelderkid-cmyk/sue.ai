#!/bin/bash

# Configuration
PROJECT_ID="gen-lang-client-0464468580"
SERVICE_ACCOUNT="289893785097-compute@developer.gserviceaccount.com"

echo "🔧 Fixing Cloud Build Permissions for $SERVICE_ACCOUNT..."

# 1. Grant Access to Cloud Build to execute builds
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudbuild.builds.builder"

# 2. Grant Access to Storage (to read the source code zip)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/storage.admin"

echo "✅ Permissions updated! Please wait 1-2 minutes for propagation, then try deploying again."
