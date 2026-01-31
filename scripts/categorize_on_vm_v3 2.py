import json
import os
import subprocess
import sys

# Configuration for VM
SOURCE_FILE = "vertex_import_FINAL.jsonl"
TARGET_BASE_DIR = "categorized_output_v7"

# Thai Month Mapping
THAI_MONTHS = {
    "มกราคม": "01", "กุมภาพันธ์": "02", "มีนาคม": "03", "เมษายน": "04", "พฤษภาคม": "05", "มิถุนายน": "06",
    "กรกฎาคม": "07", "สิงหาคม": "08", "กันยายน": "09", "ตุลาคม": "10", "พฤศจิกายน": "11", "ธันวาคม": "12",
    "ม.ค.": "01", "ก.พ.": "02", "มี.ค.": "03", "เม.ย.": "04", "พ.ค.": "05", "มิ.ย.": "06",
    "ก.ค.": "07", "ส.ค.": "08", "ก.ย.": "09", "ต.ค.": "10", "พ.ย.": "11", "ธ.ค.": "12"
}

def normalize_date(date_str):
    if not date_str or str(date_str) in ["N/A", "None", "", "-"]:
        return None
    date_str = str(date_str).strip()
    import re
    # Pattern 1: YYYY-MM-DD
    m_iso = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str)
    if m_iso:
        y, m, d = int(m_iso.group(1)), m_iso.group(2), m_iso.group(3)
        if y > 2300: y -= 543
        return f"{y:04d}-{m}-{d}"
    # Pattern 2: Thai Text
    date_str = date_str.translate(str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789"))
    for thai_m, digit_m in THAI_MONTHS.items():
        if thai_m in date_str:
            parts = re.search(r"(\d{1,2})\s+" + thai_m + r".*?(\d{4})", date_str)
            if parts:
                d, y = int(parts.group(1)), int(parts.group(2))
                if y > 2300: y -= 543
                return f"{y:04d}-{digit_m}-{d:02d}"
    return None

def clean_struct_data(data):
    if isinstance(data, dict):
        keys_to_delete = []
        for k, v in data.items():
            if "date" in k or k in ["issue_date", "publish_date"]:
                 cleaned = normalize_date(v)
                 if cleaned:
                     data[k] = cleaned
                 else:
                     keys_to_delete.append(k)
            else:
                clean_struct_data(v)
        for k in keys_to_delete:
            del data[k]
    elif isinstance(data, list):
        for item in data:
            clean_struct_data(item)

# Keyword Rules (Same as before)
RULES = {
    "law_civil": ["ป.พ.พ.", "ประมวลกฎหมายแพ่ง", "แพ่งและพาณิชย์"],
    "law_criminal": ["ป.อ.", "ประมวลกฎหมายอาญา", "กฎหมายลักษณะอาญา"],
    "law_labor": ["คุ้มครองแรงงาน", "แรงงานสัมพันธ์", "จัดตั้งศาลแรงงาน"],
    "procedure": ["ป.วิ.พ.", "ป.วิ.อ.", "วิธีพิจารณาความแพ่ง", "วิธีพิจารณาความอาญา"],
    "notices": ["พิทักษ์ทรัพย์เด็ดขาด", "ล้มละลาย", "จดทะเบียนสมาคม", "จดทะเบียนแก้ไขเพิ่มเติมข้อบังคับ", "มูลนิธิ"],
}

def get_category(doc):
    # Updated to look at fields in the NEW Schema
    struct_data = doc.get("structData", {})
    
    # Try to get title from document_meta if not directly in structData
    title = str(struct_data.get("title", ""))
    if not title:
        meta = struct_data.get("document_meta", {})
        if meta and isinstance(meta, dict):
            title = meta.get("title", "")
            
    title = (title + str(doc.get("id", ""))).lower()
    
    # Use raw_text_snippet instead of full_text
    full_text = str(struct_data.get("raw_text_snippet", "")).lower()
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
    
    # 0. Clean and Prep
    if os.path.exists(TARGET_BASE_DIR):
        print("Cleaning old output...")
        subprocess.run(f"rm -rf {TARGET_BASE_DIR}", shell=True)
    
    for cat in categories:
        os.makedirs(os.path.join(TARGET_BASE_DIR, cat), exist_ok=True)

    # 1. Check Source
    if not os.path.exists(SOURCE_FILE):
        print("📥 Downloading source from GCS...")
        subprocess.run(["gsutil", "cp", "gs://deka-legal-search-data/dataset/vertex_import_FINAL.jsonl", "."], check=True)

    print("⚡ Starting Categorization V3 (Force Flush)...")
    handles = {cat: open(os.path.join(TARGET_BASE_DIR, cat, "part_0.jsonl"), 'w', encoding='utf-8') for cat in categories}
    
    count = 0
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    doc = json.loads(line)
                    
                    # 🔥 FIX: Preserve Original StructData
                    if "structData" not in doc: 
                        doc["structData"] = {}
                        
                    struct_data = doc["structData"] # Reference to existing dict
                    
                    # 1. Identify Category (using raw_text_snippet or other fields)
                    # We might need to construct a temporary text for categorization check
                    text_for_check = str(struct_data.get("raw_text_snippet", "")) + " " + str(struct_data.get("summary", "")) + " " + str(struct_data.get("title", ""))
                    if not text_for_check.strip():
                         text_for_check = str(doc.get("id", ""))
                         
                    # Quick hack to reuse get_category logic but pass our text
                    # (Or update get_category to look at structData correctly)
                    # Let's just pass the doc, but ensure get_category looks at the right fields
                    
                    # Update get_category to support "raw_text_snippet"
                    # ... (Assuming update to get_category function below)
                    
                    cat = get_category(doc) # Ensure this function works with new schema

                    # 2. Vertex AI Requirement: Root 'content' field
                    # Map 'raw_text_snippet' (from user schema) -> 'content'
                    main_content = struct_data.get("raw_text_snippet", "")
                    if not main_content:
                         main_content = struct_data.get("summary", "") # Fallback
                    
                    doc["content"] = {
                        "mime_type": "text/plain",
                        "uri": doc.get("id", "http://fake-uri"),
                        "data": main_content if main_content else "No Content"
                    }
                    
                    # 🔥 FIX: Add '_id' field (Duplicate of 'id' to satisfy some Vertex schemas)
                    if "id" in doc and doc["id"]:
                        doc["_id"] = doc["id"]
                    else:
                        # Skip docs without ID to prevent partial failure
                        continue

                    doc["content"] = {
                        "mime_type": "text/plain",
                        "uri": doc.get("id", "http://fake-uri"),
                        "data": main_content if main_content else "No Content"
                    }
                    
                    # 🔥 FIX: Add '_id' field (Duplicate of 'id' to satisfy some Vertex schemas)
                    if "id" in doc and doc["id"]:
                        doc["_id"] = doc["id"]
                    else:
                        # Skip docs without ID to prevent partial failure
                        continue

                    # 3. Add Source Metadata (Enrich, don't overwrite)
                    struct_data["source_category"] = cat # Add categorization result
                    
                    # 🔥 FIX v7: Normalize Dates
                    clean_struct_data(struct_data)
                    if "title" not in struct_data:
                         # Try to lift title from document_meta if missing
                         meta = struct_data.get("document_meta", {})
                         if meta and "title" in meta:
                             struct_data["title"] = meta["title"]
                    
                    json_str = json.dumps(doc, ensure_ascii=False)
                    handles[cat].write(json_str + "\n")
                    
                    count += 1
                    if count % 10000 == 0:
                        print(f"Processed {count} records...")
                        for h in handles.values(): h.flush()
                        
                except Exception as e:
                    pass
    finally:
        for h in handles.values(): 
            h.flush()
            h.close()

    print(f"✅ Categorization Complete. Total: {count}")
    
    # 2. Verify Sizes Before Upload
    print("🧐 Verifying File Sizes...")
    subprocess.run(f"ls -lhR {TARGET_BASE_DIR} | head -n 20", shell=True)

    # 3. Sync to target bucket
    print("📤 Uploading Categorized V7 to gs://main_legal_data/categorized_v7/...")
    # NOTE: Using a different GCS folder to avoid confusion with empty files
    subprocess.run(["gsutil", "-m", "cp", "-r", f"{TARGET_BASE_DIR}/*", "gs://main_legal_data/categorized_v7/"], check=True)
    print("🚀 All Done!")

if __name__ == "__main__":
    process()
