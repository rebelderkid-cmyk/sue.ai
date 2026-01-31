#!/bin/bash

PROJECT_ID="gen-lang-client-0464468580"
LOCATION="global"
DATA_STORE_ID="deka-legal-data-store"
GCS_URI="gs://deka-legal-search-data/dataset"

echo "🚀 Creating Vertex AI Data Store: $DATA_STORE_ID ..."

TOKEN=$(gcloud auth print-access-token)

# 1. Create Data Store
curl -X POST \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
"https://discoveryengine.googleapis.com/v1beta/projects/$PROJECT_ID/locations/$LOCATION/collections/default_collection/dataStores?dataStoreId=$DATA_STORE_ID" \
-d '{
  "displayName": "Deka Legal Data Store",
  "industryVertical": "GENERIC",
  "solutionTypes": ["SOLUTION_TYPE_SEARCH"],
  "contentConfig": "CONTENT_REQUIRED"
}'

echo -e "\n\n⏱️ Waiting 10s for propagation..."
sleep 10

# 2. Import Data from GCS
echo "📥 Importing Data from $GCS_URI ..."

curl -X POST \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
"https://discoveryengine.googleapis.com/v1beta/projects/$PROJECT_ID/locations/$LOCATION/collections/default_collection/dataStores/$DATA_STORE_ID/branches/0/documents:import" \
-d '{
  "gcsSource": {
    "inputUris": ["'"$GCS_URI"'/*.jsonl"]
  },
  "reconciliationMode": "INCREMENTAL"
}'

echo -e "\n\n✅ Done! Check the Console."
