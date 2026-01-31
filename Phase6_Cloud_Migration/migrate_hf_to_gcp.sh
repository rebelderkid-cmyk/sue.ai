#!/bin/bash

# =================================================================================
# Name: migrate_hf_to_gcp.sh
# description: Automates the creation of a temporary Data Transfer VM in GCP
#              to act as a bridge between Hugging Face and Google Cloud Storage.
# Usage: ./migrate_hf_to_gcp.sh <attributes-gs-bucket-name>
# =================================================================================

# --- CONFIGURATION ---
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "(unset)" ]; then
    PROJECT_ID="gen-lang-client-0464468580"
fi

ZONE="asia-southeast1-b"
VM_NAME="hf-transfer-worker-$(date +%s)"
MACHINE_TYPE="e2-standard-4"
DISK_SIZE="500GB"
DISK_TYPE="pd-balanced"
GCS_BUCKET_NAME="$1"

# --- VALIDATION ---
if [ -z "$GCS_BUCKET_NAME" ]; then
    echo "Error: GCS Bucket Name is required."
    echo "Usage: ./migrate_hf_to_gcp.sh <attributes-gs-bucket-name>"
    exit 1
fi

echo "========================================================"
echo "🚀 Starting Cloud-to-Cloud Transfer Mission"
echo "--------------------------------------------------------"
echo "Project: $PROJECT_ID"
echo "VM Name: $VM_NAME"
echo "Bucket : gs://$GCS_BUCKET_NAME"
echo "Zone   : $ZONE"
echo "========================================================"

# --- CREATE STARTUP SCRIPT FILE ---
cat <<EOF > hf_transfer_startup.sh
#!/bin/bash
set -e
echo '--- [START] Startup Script ---'

# 1. Install Dependencies
apt-get update
# Install pip and git
apt-get install -y python3-pip git

# Upgrade pip ensuring we are using the system python3
python3 -m pip install -U pip
# Install hf_transfer for speed and the hub library
python3 -m pip install -U "huggingface_hub[hf_transfer]"

# Enable HF Transfer for speed
export HF_HUB_ENABLE_HF_TRANSFER=1
export HF_TOKEN="${HF_TOKEN}" # Token should be passed via environment or metadata

# 2. Prepare Directory
mkdir -p /mnt/data/downloads
cd /mnt/data/downloads

echo '--- [INFO] Starting Download from Hugging Face ---'

# USE PYTHON API DIRECTLY to avoid all CLI/PATH issues
cat <<PYTHON_EOF > download_script.py
from huggingface_hub import snapshot_download
import os

print("Starting download via Python API...")
snapshot_download(
    repo_id='open-law-data-thailand/soc-ratchakitcha',
    repo_type='dataset',
    local_dir='.',
    local_dir_use_symlinks=False
)
print("Download finished successfully.")
PYTHON_EOF

# Run the python script
python3 download_script.py

echo '--- [INFO] Download Complete. Starting Upload to GCS ---'
# Sync to GCS
gsutil -m rsync -r . gs://$GCS_BUCKET_NAME/raw_data/soc-ratchakitcha/

echo '--- [SUCCESS] Transfer Complete ---'

# 4. Self-Destruct (Stop VM)
gcloud compute instances stop $VM_NAME --zone=$ZONE
EOF

# --- CREATE VM ---
echo "Creating Worker VM... (This may take a minute)"

gcloud compute instances create "$VM_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --network-interface=network-tier=PREMIUM,subnet=default \
    --maintenance-policy=MIGRATE \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --image-family=debian-11 \
    --image-project=debian-cloud \
    --boot-disk-size="$DISK_SIZE" \
    --boot-disk-type="$DISK_TYPE" \
    --boot-disk-device-name="$VM_NAME" \
    --metadata-from-file startup-script=hf_transfer_startup.sh

# Cleanup local temp file
rm hf_transfer_startup.sh

echo "========================================================"
echo "✅ VM Created successfully!"
echo "The transfer process is now running in the background on the cloud."
echo "Monitor Logs:"
echo "  gcloud compute instances get-serial-port-output $VM_NAME --zone=$ZONE"
echo ""
echo "Delete when done:"
echo "  gcloud compute instances delete $VM_NAME --zone=$ZONE"
echo "========================================================"
