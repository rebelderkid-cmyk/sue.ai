import json
import os
import subprocess
import sys
import uuid

SOURCE = 'vertex_import_FINAL.jsonl'
TARGET_DIR = 'categorized_v7'
GCS_TARGET = 'gs://main_legal_data/categorized_v7'

def get_cat(text):
    t = text.lower()
    if 'อาญา' in t or 'ป.อ.' in t: return 'criminal'
    if 'แพ่ง' in t or 'ป.พ.พ.' in t: return 'civil'
    if 'แรงงาน' in t: return 'labor'
    return 'general'

def main():
    print('🚀 Starting V7 (Fix Missing ID)...')
    
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
    missing_id_count = 0
    
    with open(SOURCE, 'r') as f:
        for line in f:
            if not line.strip(): continue
            count += 1
            
            try:
                doc = json.loads(line)
                struct = doc.get('structData', {})
                full_text = struct.get('full_text', '') or doc.get('content', '') or doc.get('text', '') or str(struct)
                
                # Logic: ID Check (V7 FIX)
                id_str = str(doc.get('id', '')).strip()
                if not id_str:
                    id_str = f'gen_{uuid.uuid4()}'
                    missing_id_count += 1
                
                # Logic: Is Deka or Law?
                title_str = str(struct.get('title', '')).strip()
                is_deka = False
                if '/' in id_str and len(id_str) < 20 and 'gen_' not in id_str: is_deka = True
                if 'คำพิพากษา' in full_text or 'ฎีกา' in title_str: is_deka = True
                
                # Logic: Category
                cat_type = get_cat(full_text)
                if cat_type == 'general': cat_type = get_cat(title_str)
                
                prefix = 'deka' if is_deka else 'law'
                folder_name = f'{prefix}-{cat_type}'
                if folder_name not in folders: folder_name = f'{prefix}-general'
                
                new_doc = {
                    'id': id_str,
                    'content': {
                        'mime_type': 'text/plain',
                        'data': full_text
                    },
                    'structData': struct
                }
                new_doc['structData']['source_folder'] = folder_name
                
                handles[folder_name].write(json.dumps(new_doc, ensure_ascii=False) + '\n')
                
                if count % 20000 == 0:
                    print(f'Processed {count}... (Missing IDs fixed: {missing_id_count})')
                    for h in handles.values(): h.flush()
            except Exception:
                pass

    for h in handles.values(): h.close()
    
    print(f'✅ Done. Total: {count}, Fixed Missing IDs: {missing_id_count}')
    
    print(f'📤 Uploading to {GCS_TARGET}...')
    subprocess.run(f'gsutil -m cp -r {TARGET_DIR}/* {GCS_TARGET}/', shell=True)

if __name__ == '__main__':
    main()
