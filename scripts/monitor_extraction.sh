#!/bin/bash

# Configuration
VM_NAME="hf-transfer-worker-1768816536"
ZONE="asia-southeast1-b"
PROJECT_ID="gen-lang-client-0464468580"
LOG_FILE="extraction_all_files.log"

echo "========================================================"
echo "📺 Connecting to VM to monitor extraction log (OCR Mode)..."
echo "    (Press Ctrl+C to stop watching)"
echo "========================================================"

gcloud compute ssh $VM_NAME \
    --zone=$ZONE \
    --project=$PROJECT_ID \
    --command="tail -f $LOG_FILE | grep --line-buffered -E 'Processing|🚀|✅' "
