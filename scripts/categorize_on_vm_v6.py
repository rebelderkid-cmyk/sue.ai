import json
import os
import subprocess
import sys

SOURCE = 'vertex_import_FINAL.jsonl'
TARGET_DIR = 'categorized_v6_final'
GCS_TARGET = 'gs://main_legal_data/categorized_v6'

def get_cat(text):
    t = text.lower()
    if 'อาญา' in t or 'ป.อ.' in t: return 'criminal'
    if 'แพ่ง' in t or 'ป.พ.พ.' in t: return 'civil'
    if 'แรงงาน' in t: return 'labor'
    return 'general'

def main():
    print('🚀 Starting V6 PERFECT Categorizer...')
    
    # 1. Setup Dirs (8 Folders)
    if os.path.exists(TARGET_DIR): subprocess.run(f'rm -rf {TARGET_DIR}', shell=True)
    
    # Define exact folders mapping to our Data Stores + extras
    folders = [
        'deka-civil', 'deka-criminal', 'deka-labor', 'deka-general',
        'law-civil', 'law-criminal', 'law-labor', 'law-general'
    ]
    
    handles = {}
    for f in folders:
        os.makedirs(os.path.join(TARGET_DIR, f), exist_ok=True)
        handles[f] = open(os.path.join(TARGET_DIR, f, 'part_0.jsonl'), 'w', encoding='utf-8')

    # 2. Process
    count = 0
    
    with open(SOURCE, 'r') as f:
        for line in f:
            if not line.strip(): continue
            count += 1
            
            try:
                doc = json.loads(line)
                struct = doc.get('structData', {})
                full_text = struct.get('full_text', '') or doc.get('content', '') or doc.get('text', '') or str(struct)
                
                # Logic: Is Deka or Law?
                id_str = str(doc.get('id', '')).strip()
                title_str = str(struct.get('title', '')).strip()
                
                is_deka = False
                if '/' in id_str and len(id_str) < 20: is_deka = True
                if 'คำพิพากษา' in full_text or 'ฎีกา' in title_str: is_deka = True
                
                # Logic: Category
                cat_type = get_cat(full_text)
                if cat_type == 'general': cat_type = get_cat(title_str) # Double check title
                
                # Construct Folder Name
                prefix = 'deka' if is_deka else 'law'
                folder_name = f'{prefix}-{cat_type}'
                
                # Fallback
                if folder_name not in folders: folder_name = f'{prefix}-general'
                
                # Ensure Content Field (Crucial!)
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
                    print(f'Processed {count}...')
                    for h in handles.values(): h.flush()
                    
            except Exception as e:
                pass

    for h in handles.values(): h.close()
    
    print(f'✅ Done. Total: {count}')
    
    # 3. Upload
    print(f'📤 Uploading to {GCS_TARGET}...')
    subprocess.run(f'gsutil -m cp -r {TARGET_DIR}/* {GCS_TARGET}/', shell=True)

if __name__ == '__main__':
    main()
