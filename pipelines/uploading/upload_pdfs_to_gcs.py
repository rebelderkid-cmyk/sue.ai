
import os
import glob
from google.cloud import storage
from tqdm import tqdm

# Configuration
SOURCE_DIR = "/Users/rinne/Documents/Deka Scraping/DekaLatest"
BUCKET_NAME = "sue-ai-pdfs-storage"
PROJECT_ID = "gen-lang-client-0464468580"

def upload_pdfs():
    print(f"🚀 Starting PDF Upload to gs://{BUCKET_NAME}")
    
    # Initialize Client
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    
    # 1. Check if bucket exists
    if not bucket.exists():
        print(f"❌ Bucket {BUCKET_NAME} not found!")
        return

    # 2. Find Files
    pdf_files = glob.glob(os.path.join(SOURCE_DIR, "**", "*.pdf"), recursive=True)
    print(f"📦 Found {len(pdf_files)} PDF files to upload.")
    
    # 3. Upload Loop
    success_count = 0
    skipped_count = 0
    
    for file_path in tqdm(pdf_files, desc="Uploading"):
        try:
            filename = os.path.basename(file_path)
            blob = bucket.blob(filename)
            
            # Check if exists (optional skip)
            if blob.exists():
                # print(f"⏩ Skipping {filename} (already exists)")
                skipped_count += 1
                continue
                
            blob.upload_from_filename(file_path)
            # print(f"✅ Uploaded {filename}")
            success_count += 1
            
        except Exception as e:
            print(f"⚠️ Error uploading {file_path}: {e}")
            
    print(f"✅ Upload Complete!")
    print(f"   - Uploaded: {success_count}")
    print(f"   - Skipped: {skipped_count}")
    print(f"   - Total: {len(pdf_files)}")

if __name__ == "__main__":
    upload_pdfs()
