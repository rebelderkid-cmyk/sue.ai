import json
import os
import subprocess
import sys
import uuid

SOURCE = 'vertex_import_FINAL.jsonl'
TARGET_DIR = 'categorized_v8'
GCS_TARGET = 'gs://main_legal_data/categorized_v8'

def get_cat(text):
    t = text.lower()
    if 'อาญา' in t or 'ป.อ.' in t: return 'criminal'
    if 'แพ่ง' in t or 'ป.พ.พ.' in t: return 'civil'
    if 'แรงงาน' in t: return 'labor'
    return 'general'

def main():
    print('🚀 Starting V8 (CamelCase + Extra IDs)...')
    
    if os.path.exists(TARGET_DIR): subprocess.run(f'rm -rf {TARGET_DIR}', shell=True)
    
    folders = [
        'deka-civil', 'deka-criminal', 'deka-labor', 'deka-general',
        'law-civil', 'law-criminal', 'law-labor', 'law-general'
    ]
    
    handles = {}
    for f in folders:
        os.makedirs(os.path.join(TARGET_DIR, f), exist_ok=True)
        handles[f] = open(os.path.join(TARGET_DIR, f, 'part_0.jsonl'), 'w', encoding='utf-8')

    count = 0
    
    with open(SOURCE, 'r') as f:
        for line in f:
            if not line.strip(): continue
            count += 1
            
            try:
                doc = json.loads(line)
                struct = doc.get('structData', {})
                full_text = struct.get('full_text', '') or doc.get('content', '') or doc.get('text', '') or str(struct)
                
                # Logic: ID Check
                id_str = str(doc.get('id', '')).strip()
                if not id_str: id_str = f'gen_{uuid.uuid4()}'
                
                # Logic: Category
                title_str = str(struct.get('title', '')).strip()
                cat_type = get_cat(full_text)
                if cat_type == 'general': cat_type = get_cat(title_str)
                
                is_deka = False
                if '/' in id_str and len(id_str) < 20 and 'gen_' not in id_str: is_deka = True
                if 'คำพิพากษา' in full_text or 'ฎีกา' in title_str: is_deka = True
                
                prefix = 'deka' if is_deka else 'law'
                folder_name = f'{prefix}-{cat_type}'
                if folder_name not in folders: folder_name = f'{prefix}-general'
                
                # V8 FIXES:
                # 1. camelCase mimeType
                # 2. Add root level _id just in case
                new_doc = {
                    'id': id_str,
                    '_id': id_str, # Extra backup
                    'content': {
                        'mimeType': 'text/plain', # Fixed camelCase
                        'data': full_text,
                        'uri': id_str # Some docs say uri is good
                    },
                    'structData': struct
                }
                new_doc['structData']['source_folder'] = folder_name
                
                handles[folder_name].write(json.dumps(new_doc, ensure_ascii=False) + '\n')
                
                if count % 20000 == 0:
                    print(f'Processed {count}...')
                    for h in handles.values(): h.flush()
            except Exception:
                pass

    for h in handles.values(): h.close()
    print(f'✅ Done V8. Total: {count}')
    
    print(f'📤 Uploading to {GCS_TARGET}...')
    subprocess.run(f'gsutil -m cp -r {TARGET_DIR}/* {GCS_TARGET}/', shell=True)

if __name__ == '__main__':
    main()
