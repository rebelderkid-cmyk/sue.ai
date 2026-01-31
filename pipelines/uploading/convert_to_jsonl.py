import json
import os
import glob
from tqdm import tqdm

# Configuration
SOURCE_DIR = "/Users/rinne/Documents/Deka Scraping/DekaLatest"  # Absolute path to be safe
OUTPUT_FILE = "deka_dataset.jsonl"

def convert_to_jsonl():
    print(f"🚀 Starting conversion: {SOURCE_DIR} -> {OUTPUT_FILE}")
    
    # 1. Find all JSON files
    # Using recursive glob if you have subfolders, or just *.json
    files = glob.glob(os.path.join(SOURCE_DIR, "**", "*.json"), recursive=True)
    print(f"📦 Found {len(files)} JSON files.")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out_f:
        success_count = 0
        for file_path in tqdm(files, desc="Processing"):
            try:
                with open(file_path, 'r', encoding='utf-8') as in_f:
                    data = json.load(in_f)
                    
                    # Vertex AI Search requires specific fields or just raw text
                    # Ideally, we format it to match what we want to query
                    # Let's keep the original structure but flatten it to one line
                    
                    # Optional: Add metadata fields required by Vertex if strictly needed
                    # But for "Unstructured" data store, just the valid JSON object per line is enough.
                    
                    # Ensure it's a single line string
                    json_line = json.dumps(data, ensure_ascii=False)
                    out_f.write(json_line + "\n")
                    success_count += 1
            except Exception as e:
                print(f"⚠️ Error reading {file_path}: {e}")
                
    print(f"✅ Conversion Complete! Created {OUTPUT_FILE} with {success_count} records.")
    print(f"👉 Next Step: Upload this file to your Google Cloud Storage Bucket.")

if __name__ == "__main__":
    convert_to_jsonl()
