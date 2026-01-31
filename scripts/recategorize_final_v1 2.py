import json
import os
import subprocess
import uuid

# Configuration
SOURCE_GCS = "gs://main_legal_data/vertex_import_FINAL.jsonl"
LOCAL_SOURCE = "vertex_import_FINAL.jsonl"
TARGET_DIR = "categorized_final_v1"
GCS_TARGET = "gs://main_legal_data/categorized_final_v1"

def get_cat(text, title):
    t = (text + " " + title).lower()
    if 'อาญา' in t or 'ป.อ.' in t: return 'criminal'
    if 'แพ่ง' in t or 'ป.พ.พ.' in t: return 'civil'
    if 'แรงงาน' in t: return 'labor'
    return 'general'

def main():
    # Download source if not exists
    if not os.path.exists(LOCAL_SOURCE):
        print(f"📥 Downloading {SOURCE_GCS}...")
        subprocess.run(f"gsutil cp {SOURCE_GCS} {LOCAL_SOURCE}", shell=True)

    print("🚀 Starting Final Categorization (Zero-Mutation Mode)...")
    
    # Prep folders
    categories = ['civil', 'criminal', 'labor', 'general']
    types = ['law', 'deka']
    folders = [f"{t}-{c}" for t in types for c in categories]
    
    handles = {}
    if os.path.exists(TARGET_DIR):
        subprocess.run(f"rm -rf {TARGET_DIR}", shell=True)
    
    for f in folders:
        os.makedirs(os.path.join(TARGET_DIR, f), exist_ok=True)
        handles[f] = open(os.path.join(TARGET_DIR, f, 'part_0.jsonl'), 'w', encoding='utf-8')

    count = 0
    with open(LOCAL_SOURCE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            try:
                doc = json.loads(line)
                struct = doc.get('structData', {})
                # Extract text for categorization
                text = struct.get('raw_text_snippet', '') or struct.get('text', '') or ""
                title = struct.get('document_meta', {}).get('title', '') or ""
                
                # Determine Category
                cat = get_cat(text, title)
                
                # Determine Type (Deka vs Law)
                id_str = str(doc.get('id', ''))
                is_deka = False
                if 'deka' in id_str.lower() or '/' in id_str or 'คำพิพากษา' in text or 'ฎีกา' in title:
                    is_deka = True
                
                prefix = 'deka' if is_deka else 'law'
                folder_name = f"{prefix}-{cat}"
                
                # PRESERVE ORIGINAL SCHEMA
                # We only keep id and structData exactly as they were in vertex_import_FINAL.jsonl
                new_doc = {
                    "id": doc.get("id"),
                    "structData": struct
                }
                
                handles[folder_name].write(json.dumps(new_doc, ensure_ascii=False) + '\n')
                count += 1
                
                if count % 10000 == 0:
                    print(f"Processed {count} records...")
            except Exception as e:
                print(f"Error processing record: {e}")

    # Close all files
    for h in handles.values():
        h.close()

    print(f"✅ Categorization Complete. Total: {count}")
    print(f"📤 Uploading to {GCS_TARGET}...")
    subprocess.run(f"gsutil -m cp -r {TARGET_DIR}/* {GCS_TARGET}/", shell=True)
    print("✨ Process Finished!")

if __name__ == "__main__":
    main()
