import os
import json
import glob
from collections import defaultdict

OCR_ROOT = "/mnt/data/downloads/ocr/iapp"

TARGET_KEYWORDS = [
    "คำพิพากษาศาลฎีกา",
    "พระราชบัญญัติ",
    "พระราชกฤษฎีกา",
    "กฎกระทรวง",
    "ประกาศ"
]

def get_all_strings(obj):
    """Recursively extract all strings from a JSON object."""
    text = []
    if isinstance(obj, dict):
        for v in obj.values():
            text.extend(get_all_strings(v))
    elif isinstance(obj, list):
        for item in obj:
            text.extend(get_all_strings(item))
    elif isinstance(obj, str):
        text.append(obj)
    return text

def scan_high_value_docs():
    stats = defaultdict(int)
    total_scanned = 0
    matched_count = 0
    
    print("🔎 Scanning for High Value Documents (Universal Mode)...")
    
    jsonl_files = glob.glob(os.path.join(OCR_ROOT, "**/*.jsonl"), recursive=True)
    
    # Optional: Log the first few matches for debugging
    debug_log = []
    
    for file_path in jsonl_files:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    total_scanned += 1
                    data = json.loads(line)
                    
                    # Universal Text Extraction
                    all_text_list = get_all_strings(data)
                    full_text = " ".join(all_text_list)[:2000] # Check first 2000 chars combined
                    
                    found_cat = None
                    for kw in TARGET_KEYWORDS:
                        if kw in full_text:
                            found_cat = kw
                            break
                    
                    if found_cat:
                        stats[found_cat] += 1
                        matched_count += 1
                        if len(debug_log) < 5:
                            debug_log.append(f"[{found_cat}] {full_text[:100]}...")
                            
                except: continue
                
    print("\n📊 --- High Value Scan Results (Universal) ---")
    print(f"Total Documents Scanned: {total_scanned:,}")
    print(f"Target Documents Found:  {matched_count:,} ({(matched_count/total_scanned*100):.1f}%)")
    
    print("\n📂 Breakdown by Category:")
    for kw in TARGET_KEYWORDS:
        print(f"   - {kw}: {stats[kw]:,}")
        
    print("\n🐛 Example Matches:")
    for log in debug_log:
        print(f"   {log}")

if __name__ == "__main__":
    scan_high_value_docs()
