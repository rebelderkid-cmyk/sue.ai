#!/bin/bash

BUCKET="gs://deka-legal-search-data"
echo "🚀 Starting GCS Sync to $BUCKET..."

# 1. Sync PDFs (Reference) - Only filtered PDFs if possible? 
# Or just sync all PDFs inside /mnt/data/downloads (Zip extraction required?)
# For now, let's assume we want to sync the processed JSONL first.

# 2. Sync The Knowledge Graph JSONL
echo "📤 Uploading Knowledge Graph JSONL..."
# We upload it with a timestamp or unique name so Vertex treats it as a batch
gsutil -m cp /home/rinne/law_knowledge_graph_final.jsonl $BUCKET/dataset/import_$(date +%Y%m%d_%H%M).jsonl

echo "✅ JSONL Sync Initial Batch Complete."

# Note: For PDF sync, it's tricky because PDFs are inside ZIPs.
# We might need to write a script to extract & upload ONLY the interesting PDFs to save space/time.
