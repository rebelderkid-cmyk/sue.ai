import os
import sys
import concurrent.futures
import json
import subprocess
import shutil
import easyocr
import io
import time
from threading import Lock
from pdf2image import convert_from_path

# --- CONFIGURATION (EASYOCR INDEXING MODE) ---
MAX_WORKERS = 20            # Reduced to prevent initialization deadlock
CONCURRENT_ZIPS = 3         # Keep zip pipelining
SURVEY_REPORT = "/home/rinne/law_index_easyocr.jsonl"
PROGRESS_FILE = "/home/rinne/easyocr_progress.txt"
ZIP_ROOT = "/mnt/data/downloads/zip"
TEMP_ROOT = "/home/rinne/temp_index"

# Focus Keywords to flag High Value
TARGET_KEYWORDS = [
    "รัฐธรรมนูญ",
    "พระราชบัญญัติ",
    "พระราชกำหนด",
    "พระราชกฤษฎีกา",
    "กฎกระทรวง"
]

report_lock = Lock()

# Global variable for the worker process
READER = None

def init_worker():
    """Initialize the EasyOCR reader once per process."""
    global READER
    try:
        # print(f"Worker {os.getpid()} initializing...", flush=True)
        READER = easyocr.Reader(['th', 'en'], gpu=False, verbose=False)
        # print(f"Worker {os.getpid()} ready!", flush=True)
    except Exception as e:
        print(f"Worker init failed: {e}", flush=True)

def process_file_task(file_path, year, zip_name):
    """
    Task to be executed by the worker process.
    Uses the pre-initialized global READER.
    """
    global READER
    if READER is None:
        return None

    try:
        # 1. Convert first page to image
        images = convert_from_path(file_path, last_page=1)
        if not images: return None
        
        img_byte_arr = io.BytesIO()
        images[0].save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()

        # 2. EasyOCR Scan
        result_text_list = READER.readtext(img_bytes, detail=0)
        text_content = " ".join(result_text_list)
        
        # 3. Categorize
        found_cats = [kw for kw in TARGET_KEYWORDS if kw in text_content]
        
        # 4. Construct Metadata Record
        record = {
            "file_name": os.path.basename(file_path),
            "year": year,
            "zip_source": zip_name,
            "categories": found_cats,
            "is_high_value": len(found_cats) > 0,
            "preview_text": text_content[:500],
            "processed_at": time.time()
        }
        return record
        
    except Exception as e:
        # print(f"Error processing {file_path}: {e}")
        return None

def process_zip_indexing(zip_path, executor, year):
    zip_name = os.path.basename(zip_path)
    temp_dir = os.path.join(TEMP_ROOT, zip_name.replace('.zip', ''))
    os.makedirs(temp_dir, exist_ok=True)
    
    subprocess.run(["unzip", "-o", "-q", zip_path, "-d", temp_dir], check=False)
    
    pdfs = []
    for root, _, files in os.walk(temp_dir):
        for f in files:
            if f.lower().endswith('.pdf'):
                pdfs.append(os.path.join(root, f))
    
    # Batch write results is too slow for realtime dashboard, switching to immediate write
    # We still iterate futures, but we write as they come in
    if pdfs:
        futures = [executor.submit(process_file_task, p, year, zip_name) for p in pdfs]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            res = future.result()
            if res:
                # Immediate write with lock
                with report_lock:
                    with open(SURVEY_REPORT, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(res, ensure_ascii=False) + "\n")
                        f.flush() # Force write to disk
            
            # Print progress every 10 files to avoid log flooding but keep it alive
            if i % 10 == 0:
                print(f"   Processed {i+1}/{len(pdfs)} in {zip_name}...", flush=True)

    shutil.rmtree(temp_dir)
    with report_lock:
         with open(PROGRESS_FILE, 'a') as f: f.write(zip_path + "\n")
    
    return len(pdfs)

def main():
    if os.path.exists(TEMP_ROOT):
        shutil.rmtree(TEMP_ROOT)
    os.makedirs(TEMP_ROOT, exist_ok=True)

    processed_zips = set()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            processed_zips = set(line.strip() for line in f)

    all_zips = []
    for root, _, files in os.walk(ZIP_ROOT):
        for f in files:
            if f.lower().endswith('.zip'):
                path = os.path.join(root, f)
                if path not in processed_zips:
                    year = os.path.basename(root) 
                    all_zips.append((path, year))
    
    all_zips.sort(key=lambda x: x[1], reverse=True) # Process newest first
    
    print(f"🧠 [EASYOCR INDEXING MODE] Scanning {len(all_zips)} Zips using 80 Cores...", flush=True)
    
    # Using ProcessPoolExecutor with initializer to load model ONCE per worker
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS, initializer=init_worker) as process_executor:
        # Using ThreadPool just to manage Zip extraction flow, feeding the process executor
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_ZIPS) as zip_thread_manager:
            futures = [zip_thread_manager.submit(process_zip_indexing, zp[0], process_executor, zp[1]) for zp in all_zips]
            for _ in concurrent.futures.as_completed(futures): pass

if __name__ == "__main__":
    main()
