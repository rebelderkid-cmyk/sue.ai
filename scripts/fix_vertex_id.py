import json
import os

INPUT_FILE = "data/local_import/vertex_ready_upload.jsonl"
OUTPUT_FILE = "data/local_import/vertex_ready_fixed_id.jsonl"

def fix_vertex_ids():
    print(f"🔄 Fixing IDs in {INPUT_FILE}...")
    
    if not os.path.exists(INPUT_FILE):
        print("❌ Input file not found!")
        return

    count = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as fin, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:
        
        for line in fin:
            try:
                data = json.loads(line.strip())
                
                # FIX: Remove .pdf from ID to match [a-zA-Z0-9-_]*
                raw_id = data.get('id', "")
                clean_id = raw_id.replace('.pdf', '').replace('.', '_') # Replace any other dots just in case
                
                data['id'] = clean_id
                
                # Also ensure internal structData has the clean ID if needed (optional but good practice)
                if 'structData' in data:
                    data['structData']['id'] = clean_id

                fout.write(json.dumps(data, ensure_ascii=False) + '\n')
                count += 1
            except Exception as e:
                print(f"⚠️ Skip line: {e}")
    
    print(f"✅ Fixed {count} IDs. New file: {OUTPUT_FILE}")

if __name__ == "__main__":
    fix_vertex_ids()
