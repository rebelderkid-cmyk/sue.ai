import json
import os
import glob
import subprocess

# Configuration for VM
SOURCE_FILE = "vertex_import_FINAL.jsonl"
TARGET_BASE_DIR = "categorized_output"

# Keyword Rules
RULES = {
    "law_civil": ["ป.พ.พ.", "ประมวลกฎหมายแพ่ง", "แพ่งและพาณิชย์"],
    "law_criminal": ["ป.อ.", "ประมวลกฎหมายอาญา", "กฎหมายลักษณะอาญา"],
    "law_labor": ["คุ้มครองแรงงาน", "แรงงานสัมพันธ์", "จัดตั้งศาลแรงงาน"],
    "procedure": ["ป.วิ.พ.", "ป.วิ.อ.", "วิธีพิจารณาความแพ่ง", "วิธีพิจารณาความอาญา"],
    "notices": ["พิทักษ์ทรัพย์เด็ดขาด", "ล้มละลาย", "จดทะเบียนสมาคม", "จดทะเบียนแก้ไขเพิ่มเติมข้อบังคับ", "มูลนิธิ"],
}

def get_category(doc):
    struct_data = doc.get("structData", {})
    title = str(struct_data.get("title", "")).lower() + str(doc.get("id", "")).lower()
    full_text = str(struct_data.get("full_text", "")).lower()
    content = title + " " + full_text
    
    is_deka = "deka" in title or "คำพิพากษาศาลฎีกา" in full_text
    
    for kw in RULES["notices"]:
        if kw.lower() in content: return "notices"
            
    for kw in RULES["law_labor"]:
        if kw.lower() in content: return "deka_labor" if is_deka else "law_labor"
            
    for kw in RULES["law_civil"]:
        if kw.lower() in content: return "deka_civil" if is_deka else "law_civil"
            
    for kw in RULES["law_criminal"]:
        if kw.lower() in content: return "deka_criminal" if is_deka else "law_criminal"

    for kw in RULES["procedure"]:
        if kw.lower() in content: return "procedure"

    return "deka_general" if is_deka else "others"

def process():
    categories = ["law_civil", "law_criminal", "law_labor", "deka_civil", "deka_criminal", "deka_labor", "deka_general", "procedure", "notices", "others"]
    for cat in categories:
        os.makedirs(os.path.join(TARGET_BASE_DIR, cat), exist_ok=True)

    # 1. Download source from GCS
    print("📥 Downloading source from GCS...")
    subprocess.run(["gsutil", "cp", "gs://deka-legal-search-data/dataset/vertex_import_FINAL.jsonl", "."], check=True)

    print("⚡ Starting Categorization...")
    # Open all file handles at once for speed (context managers)
    handles = {cat: open(os.path.join(TARGET_BASE_DIR, cat, "part_0.jsonl"), 'w', encoding='utf-8') for cat in categories}
    
    count = 0
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    doc = json.loads(line)
                    cat = get_category(doc)
                    handles[cat].write(line)
                    count += 1
                    if count % 10000 == 0:
                        print(f"Processed {count} records...")
                except Exception as e:
                    pass
    finally:
        for h in handles.values(): h.close()

    print(f"✅ Categorization Complete. Total: {count}")
    
    # 3. Sync to target bucket
    print("📤 Syncing to gs://main_legal_data/categorized/...")
    subprocess.run(["gsutil", "-m", "cp", "-r", f"{TARGET_BASE_DIR}/*", "gs://main_legal_data/categorized/"], check=True)
    print("🚀 All Done!")

if __name__ == "__main__":
    process()
