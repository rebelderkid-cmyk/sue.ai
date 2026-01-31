import json
import os
import subprocess

INPUT_FILE = "/home/rinne/law_knowledge_graph_final.jsonl"
OUTPUT_FILE = "/home/rinne/vertex_ready.jsonl"
GCS_BUCKET = "gs://deka-legal-search-data/dataset"

def convert_and_upload():
    print(f"🔄 Reading {INPUT_FILE}...")
    
    if not os.path.exists(INPUT_FILE):
        print("❌ Input file not found!")
        return

    count = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as fin, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:
        
        for line in fin:
            try:
                data = json.loads(line.strip())
                
                # Check if already converted (has structData)
                if 'structData' in data:
                    fout.write(line) # Write as is
                    continue

                # Conversion Logic
                # Vertex ID: Must match [a-zA-Z0-9-_]* (No dots!)
                raw_filename = data.get('file_name', f'doc_{count}')
                clean_id = raw_filename.replace('.pdf', '').replace('.', '_')
                
                vertex_record = {
                    "id": clean_id,
                    "structData": data
                }
                
                fout.write(json.dumps(vertex_record, ensure_ascii=False) + '\n')
                count += 1
            except Exception as e:
                print(f"⚠️ Skip line: {e}")

    print(f"✅ Converted {count} records locally.")
    
    # Upload
    gcs_target = f"{GCS_BUCKET}/vertex_import_FINAL.jsonl"
    print(f"📤 Uploading to {gcs_target}...")
    subprocess.run(["gsutil", "cp", OUTPUT_FILE, gcs_target], check=True)
    print("🎉 Done! You can use this file in Vertex AI Console now.")

if __name__ == "__main__":
    convert_and_upload()
