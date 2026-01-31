import json
import os
import glob
from pathlib import Path

# Configuration
SOURCE_DIR = "/Users/rinne/Documents/Deka Scraping/data/processed"
TARGET_BASE_DIR = "/Users/rinne/Documents/Deka Scraping/data/categorized"

# Keyword Rules
RULES = {
    "law_civil": ["ป.พ.พ.", "ประมวลกฎหมายแพ่ง", "แพ่งและพาณิชย์"],
    "law_criminal": ["ป.อ.", "ประมวลกฎหมายอาญา", "กฎหมายลักษณะอาญา"],
    "law_labor": ["คุ้มครองแรงงาน", "แรงงานสัมพันธ์", "จัดตั้งศาลแรงงาน"],
    "procedure": ["ป.วิ.พ.", "ป.วิ.อ.", "วิธีพิจารณาความแพ่ง", "วิธีพิจารณาความอาญา"],
    "notices": ["พิทักษ์ทรัพย์เด็ดขาด", "ล้มละลาย", "จดทะเบียนสมาคม", "จดทะเบียนแก้ไขเพิ่มเติมข้อบังคับ", "มูลนิธิ"],
}

def get_category(doc):
    title = doc.get("structData", {}).get("title", "").lower() + doc.get("id", "").lower()
    full_text = doc.get("structData", {}).get("full_text", "").lower()
    content = title + " " + full_text
    
    is_deka = "deka" in title or "คำพิพากษาศาลฎีกา" in full_text
    
    # Check for Noise/Notices first
    for kw in RULES["notices"]:
        if kw.lower() in content:
            return "notices"
            
    # Check for Labor
    for kw in RULES["law_labor"]:
        if kw.lower() in content:
            return f"deka_labor" if is_deka else "law_labor"
            
    # Check for Civil
    for kw in RULES["law_civil"]:
        if kw.lower() in content:
            return f"deka_civil" if is_deka else "law_civil"
            
    # Check for Criminal
    for kw in RULES["law_criminal"]:
        if kw.lower() in content:
            return f"deka_criminal" if is_deka else "law_criminal"

    # Check for Procedure
    for kw in RULES["procedure"]:
        if kw.lower() in content:
            return "procedure"

    if is_deka:
        return "deka_general"
        
    return "others"

def process_files():
    # Ensure target directories exist
    categories = ["law_civil", "law_criminal", "law_labor", "deka_civil", "deka_criminal", "deka_labor", "deka_general", "procedure", "notices", "others"]
    for cat in categories:
        os.makedirs(os.path.join(TARGET_BASE_DIR, cat), exist_ok=True)

    jsonl_files = glob.glob(os.path.join(SOURCE_DIR, "*.jsonl"))
    print(f"Found {len(jsonl_files)} files to process.")

    for file_path in jsonl_files:
        print(f"Processing {os.path.basename(file_path)}...")
        
        # We'll buffer the output to avoid too many file handles
        buffers = {cat: [] for cat in categories}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        doc = json.loads(line)
                        cat = get_category(doc)
                        buffers[cat].append(line)
                    except Exception as e:
                        print(f"Error parsing line: {e}")
            
            # Write buffers
            for cat, lines in buffers.items():
                if not lines: continue
                output_file = os.path.join(TARGET_BASE_DIR, cat, os.path.basename(file_path))
                with open(output_file, 'w', encoding='utf-8') as out_f:
                    out_f.writelines(lines)
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

if __name__ == "__main__":
    process_files()
    print("Categorization Complete!")
