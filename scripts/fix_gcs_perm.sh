#!/bin/bash
PROJECT_ID="gen-lang-client-0464468580"
BUCKET="gs://deka-legal-search-data"

# Get Project Number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
echo "Project Number: $PROJECT_NUMBER"

# Vertex AI Agent Builder Service Agent (Discovery Engine)
# 1. Discovery Engine SA (Search)
SA_DISCO="service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
echo "Granting roles/storage.objectViewer to $SA_DISCO..."
gcloud storage buckets add-iam-policy-binding $BUCKET --member="serviceAccount:$SA_DISCO" --role="roles/storage.objectViewer"

# 2. Vertex AI Platform SA (General AI)
SA_AI="service-${PROJECT_NUMBER}@gcp-sa-aiplatform.iam.gserviceaccount.com"
echo "Granting roles/storage.objectViewer to $SA_AI..."
gcloud storage buckets add-iam-policy-binding $BUCKET --member="serviceAccount:$SA_AI" --role="roles/storage.objectViewer"

# 3. Default Compute Engine SA (Just in case user is creating from VM context?)
# SA_COMPUTE="{project_number}-compute@developer.gserviceaccount.com"

echo "✅ Done! Please try creating the Data Store again."
