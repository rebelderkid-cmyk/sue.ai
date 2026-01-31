import json
import os
import glob
from tqdm import tqdm
import base64

# Configuration
SOURCE_DIR = "/Users/rinne/Documents/Deka Scraping/DekaLatest"
OUTPUT_FILE = "deka_dataset_v2.jsonl"

def convert_to_jsonl():
    print(f"🚀 Starting conversion (Vertex AI Compatible): {SOURCE_DIR} -> {OUTPUT_FILE}")
    
    files = glob.glob(os.path.join(SOURCE_DIR, "**", "*.json"), recursive=True)
    print(f"📦 Found {len(files)} JSON files.")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out_f:
        success_count = 0
        for file_path in tqdm(files, desc="Processing"):
            try:
                with open(file_path, 'r', encoding='utf-8') as in_f:
                    data = json.load(in_f)
                    
                    # 1. Generate ID (Safe string)
                    # filename: Deka_10-2566_(Ref701475).pdf -> ID: Deka_10-2566
                    filename = data.get("filename", "")
                    doc_id = filename.replace(".pdf", "").replace(" ", "_").replace("(", "").replace(")", "")
                    if not doc_id:
                        continue

                    # 2. Extract Metadata (Flattening for easier filtering in Vertex)
                    meta = data.get("metadata", {})
                    extraction = meta.get("extraction_data", {})
                    
                    year = "Unknown"
                    if "case_no_full" in extraction:
                        parts = extraction["case_no_full"].split("/")
                        if len(parts) > 1:
                            year = parts[-1]
                    
                    outcome = "Unknown"
                    if extraction.get("outcome"):
                        outcome = extraction["outcome"][0] if isinstance(extraction["outcome"], list) else str(extraction["outcome"])

                    # 3. Text Content
                    raw_text = data.get("raw_text", "")

                    # 4. Construct Vertex AI Document Object
                    # Ref: https://cloud.google.com/generative-ai-app-builder/docs/prepare-data/unstructured
                    vertex_doc = {
                        "id": doc_id,
                        "structData": {
                            "filename": filename,
                            "year": year,
                            "outcome": outcome,
                            "laws": extraction.get("laws_found", []),
                            "full_text": raw_text  # We will use this for search instead of 'content'
                        }
                        # "content": { ... } REMOVED: Data Store is Structured, so we strictly use structData
                    }
                    
                    # Write to JSONL
                    json_line = json.dumps(vertex_doc, ensure_ascii=False)
                    out_f.write(json_line + "\n")
                    success_count += 1
                    
            except Exception as e:
                # print(f"⚠️ Error processing {file_path}: {e}")
                pass
                
    print(f"✅ Conversion Complete! Created {OUTPUT_FILE} with {success_count} valid records.")
    print(f"👉 Next Step: Upload '{OUTPUT_FILE}' to GCS and Import again.")

if __name__ == "__main__":
    convert_to_jsonl()
