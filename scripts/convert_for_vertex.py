import json
import sys
import os

def convert_to_vertex_format(input_path, output_path):
    print(f"🔄 Converting {input_path} -> {output_path} ...")
    count = 0
    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:
        
        for line in fin:
            try:
                data = json.loads(line.strip())
                
                # Extract ID from filename (or generate one)
                doc_id = data.get('file_name', f'doc_{count}')
                
                # Construct Vertex AI Structure
                vertex_obj = {
                    "id": doc_id,
                    "structData": data  # Nest everything inside 'structData'
                }
                
                # Additional: If you want to index 'content' specifically for search
                # vertex_obj["content"] = {"mimeType": "text/plain", "uri": ...} 
                # But structData is usually enough for structured search.

                fout.write(json.dumps(vertex_obj, ensure_ascii=False) + '\n')
                count += 1
            except Exception as e:
                print(f"⚠️ Skipping error line: {e}")
    
    print(f"✅ Converted {count} records. Ready for upload!")

if __name__ == "__main__":
    # Auto-detect input file in data/local_import/
    input_dir = "data/local_import"
    files = [f for f in os.listdir(input_dir) if f.endswith(".jsonl") and not f.startswith("vertex_ready")]
    
    if not files:
        print("❌ No input JSONL found in data/local_import/")
        sys.exit(1)
        
    input_file = os.path.join(input_dir, files[0]) # Pick first one
    output_file = os.path.join(input_dir, "vertex_ready_upload.jsonl")
    
    convert_to_vertex_format(input_file, output_file)
