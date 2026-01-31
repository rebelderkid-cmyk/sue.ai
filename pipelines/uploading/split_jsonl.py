import os

# Configuration
INPUT_FILE = "deka_dataset_v2.jsonl"  # It's in the root
CHUNK_SIZE_MB = 50  # Split into 50MB chunks (User Request: Test Size)
OUTPUT_PREFIX = "Phase6_Cloud_Migration/deka_dataset_part_"

def split_file():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ File not found: {INPUT_FILE}")
        return

    print(f"🔪 Splitting '{INPUT_FILE}' into {CHUNK_SIZE_MB}MB chunks...")
    
    chunk_size = CHUNK_SIZE_MB * 1024 * 1024
    file_number = 1
    
    with open(INPUT_FILE, 'rb') as f:
        chunk = f.readlines(chunk_size)
        while chunk:
            output_filename = f"{OUTPUT_PREFIX}{file_number:03d}.jsonl"
            with open(output_filename, 'wb') as chunk_file:
                chunk_file.writelines(chunk)
            
            print(f"✅ Created: {output_filename}")
            file_number += 1
            chunk = f.readlines(chunk_size)
            
    print("🎉 Splitting Complete! Upload these part files to GCS.")

if __name__ == "__main__":
    split_file()
