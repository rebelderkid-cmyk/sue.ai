#!/bin/bash

# =================================================================================
# Name: migrate_hf_to_gcp.sh
# description: Automates the creation of a temporary Data Transfer VM in GCP
#              to act as a bridge between Hugging Face and Google Cloud Storage.
#              This avoids using local bandwidth for 175GB+ of data.
# Usage: ./migrate_hf_to_gcp.sh <attributes-gs-bucket-name>
# Dependencies: gcloud CLI (installed and authenticated)
# =================================================================================

# --- CONFIGURATION (Change these or set as env vars) ---
PROJECT_ID=$(gcloud config get-value project)
ZONE="asia-southeast1-b"    # Close to Thailand for lower latency if source is relevant, or just good default
VM_NAME="hf-transfer-worker-$(date +%s)"
MACHINE_TYPE="e2-standard-4" # 4 vCPUs, 16GB RAM (Good balance for parallel download/upload)
DISK_SIZE="500GB"           # 175GB data + buffer + OS
DISK_TYPE="pd-balanced"
GCS_BUCKET_NAME="$1"        # Pass bucket name as first argument

# --- VALIDATION ---
if [ -z "$GCS_BUCKET_NAME" ]; then
    echo "Error: GCS Bucket Name is required."
    echo "Usage: ./migrate_hf_to_gcp.sh <attributes-gs-bucket-name>"
    echo "Example: ./migrate_hf_to_gcp.sh my-legal-data-bucket"
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

# --- 1. CREATE VM WITH DATA TRANSFER SCRIPT ---
# We inject the logic directly into the startup-script so it runs automatically upon boot.
# The script will:
# 1. Install dependencies (pip, hf_transfer, huggingface-cli)
# 2. Authenticate (Optional: if repo is public, no auth needed. soc-ratchakitcha is public)
# 3. Download data to high-speed disk
# 4. Upload to GCS
# 5. Shut down

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
    --metadata=startup-script="#!/bin/bash
set -e
echo '--- [START] Startup Script ---'

# 1. Install Dependencies
apt-get update
apt-get install -y python3-pip git
pip3 install -U \"huggingface_hub[cli]\"

# Enable HF Transfer for speed (uses Rust, very fast)
export HF_HUB_ENABLE_HF_TRANSFER=1

# 2. Prepare Directory
mkdir -p /mnt/data/downloads
cd /mnt/data/downloads

echo '--- [INFO] Starting Download from Hugging Face ---'
# Download ONLY the PDF files to save time if you don't need all versions, 
# or download everything if you want a full mirror.
# The user asked for 'Download files ... to DB', implying data.
# We will download the entire repository to be safe, or we could filter.
# Given 175GB constraint, we assume full sync.

# Download command (Public repo, no token needed)
huggingface-cli download open-law-data-thailand/soc-ratchakitcha \
    --repo-type dataset \
    --local-dir . \
    --local-dir-use-symlinks False

echo '--- [INFO] Download Complete. Starting Upload to GCS ---'

# 3. Sync to GCS
# -m = multi-threaded/parallel
# rsync -r = recursive sync
gsutil -m rsync -r . gs://$GCS_BUCKET_NAME/raw_data/soc-ratchakitcha/

echo '--- [SUCCESS] Transfer Complete ---'

# 4. Self-Destruct / Shutdown
# We won't delete the VM automatically to allow debugging if something fails.
# Instead, we'll stop it.
gcloud compute instances stop $VM_NAME --zone=$ZONE
"

echo "========================================================"
echo "✅ VM Created successfully!"
echo "The transfer process is now running in the background on the cloud."
echo "You can monitor the progress by viewing the logs:"
echo ""
echo "  gcloud compute instances get-serial-port-output $VM_NAME --zone=$ZONE"
echo ""
echo "When you see '--- [SUCCESS] Transfer Complete ---', the VM will limit itself."
echo "Don't forget to DELETE the VM after verifying the data in GCS to avoid costs!"
echo ""
echo "  gcloud compute instances delete $VM_NAME --zone=$ZONE"
echo "========================================================"
