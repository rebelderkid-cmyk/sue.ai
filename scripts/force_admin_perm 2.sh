#!/bin/bash
PROJECT_ID="gen-lang-client-0464468580"
BUCKET="gs://deka-legal-search-data"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

SA_DISCO="service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
SA_AI="service-${PROJECT_NUMBER}@gcp-sa-aiplatform.iam.gserviceaccount.com"

echo "🔥 Forcing 'Storage Admin' role for Vertex AI Service Accounts..."

# Discovery Engine
gcloud storage buckets add-iam-policy-binding $BUCKET \
    --member="serviceAccount:$SA_DISCO" \
    --role="roles/storage.admin"

# AI Platform
gcloud storage buckets add-iam-policy-binding $BUCKET \
    --member="serviceAccount:$SA_AI" \
    --role="roles/storage.admin"

echo "✅ UPGRADED to Storage Admin! Try creating Data Store NOW."
