#!/bin/bash

# Configuration (Project ID provided by user)
PROJECT_ID="gen-lang-client-0464468580"
BUCKET_NAME="gs://sue-ai-pdfs-storage"

echo "========================================================"
echo "🔍 Checking Google Cloud Status..."
echo "========================================================"

echo ""
echo "📂 [1/2] Storage Bucket ($BUCKET_NAME):"
gcloud storage ls $BUCKET_NAME/ --project=$PROJECT_ID || echo "❌ Failed to list bucket (Check permissions or name)"

echo ""
echo "💻 [2/2] Virtual Machines (Compute Engine):"
gcloud compute instances list --project=$PROJECT_ID || echo "❌ Failed to list instances"

echo ""
echo "========================================================"
echo "✅ Check Complete."
