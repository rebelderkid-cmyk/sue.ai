import json
import subprocess
import os

# CONFIGURATION
SOURCE_GS_URL = "gs://main_legal_data/vertex_import_FINAL.jsonl"
TARGET_GS_BASE = "gs://main_legal_data/categorized"
LOCAL_OUT_DIR = "/home/rinne/categorized_output"

CATEGORIES = {
    "civil": ["ป.พ.พ.", "ประมวลกฎหมายแพ่ง", "แพ่งและพาณิชย์"],
    "criminal": ["ป.อ.", "ประมวลกฎหมายอาญา", "กฎหมายลักษณะอาญา"],
    "labor": ["คุ้มครองแรงงาน", "แรงงานสัมพันธ์", "จัดตั้งศาลแรงงาน"],
    "procedure": ["ป.วิ.พ.", "ป.วิ.อ.", "วิธีพิจารณาความแพ่ง", "วิธีพิจารณาความอาญา"],
    "notices": ["พิทักษ์ทรัพย์", "ล้มละลาย", "จดทะเบียนสมาคม", "มูลนิธิ"],
}

def get_category(doc):
    # Search in multiple possible fields
    text_to_scan = ""
    # Try structData
    struct_data = doc.get("structData", {})
    text_to_scan += str(struct_data)
    # Try content
    text_to_scan += doc.get("content", "")
    
    content_lower = text_to_scan.lower()
    for cat, keywords in CATEGORIES.items():
        if any(kw.lower() in content_lower for kw in keywords):
            return cat
    return "others"

def stream_categorize():
    if not os.path.exists(LOCAL_OUT_DIR):
        os.makedirs(LOCAL_OUT_DIR)
        
    # Open local file handles for each category
    files = {cat: open(os.path.join(LOCAL_OUT_DIR, f"{cat}.jsonl"), "w", encoding="utf-8") for cat in CATEGORIES}
    files["others"] = open(os.path.join(LOCAL_OUT_DIR, "others.jsonl"), "w", encoding="utf-8")
    
    print(f"🚀 Streaming from {SOURCE_GS_URL}...")
    
    # Use gsutil cat to stream the large file
    cmd = ["gsutil", "cat", SOURCE_GS_URL]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, bufsize=1)
    
    count = 0
    try:
        for line in process.stdout:
            if not line.strip(): continue
            try:
                doc = json.loads(line)
                cat = get_category(doc)
                files[cat].write(line)
                count += 1
                
                if count % 10000 == 0:
                    print(f"✅ Processed {count} records...", flush=True)
                    # Periodically flush to disk
                    for f in files.values(): f.flush()
            except Exception as e:
                continue
    finally:
        # Close all files
        for f in files.values():
            f.close()
        process.terminate()

    print(f"🎉 Stream finished. Total: {count}. Starting GCS Upload...")
    
    # Sync categories to GCS
    for cat in list(CATEGORIES.keys()) + ["others"]:
        local_file = os.path.join(LOCAL_OUT_DIR, f"{cat}.jsonl")
        if os.path.exists(local_file) and os.path.getsize(local_file) > 0:
            print(f"Uploading {cat}...")
            remote_url = f"{TARGET_GS_BASE}/{cat}/legal_import_part.jsonl"
            subprocess.run(["gsutil", "-m", "cp", local_file, remote_url])

if __name__ == "__main__":
    stream_categorize()
    print("Done!")
