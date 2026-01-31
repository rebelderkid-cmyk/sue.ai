import re
import json
import os
import sys
import concurrent.futures
from datetime import datetime
import subprocess
import shutil
import time
from threading import Lock
from pypdf import PdfReader

# --- CONFIGURATION (SURVEY MODE) ---
MAX_WORKERS = 120           # Back to FULL POWER for Survey
CONCURRENT_ZIPS = 3
SURVEY_REPORT = "/home/rinne/law_survey_report.json"
PROGRESS_FILE = "/home/rinne/survey_progress.txt"
ZIP_ROOT = "/mnt/data/downloads/zip"
TEMP_ROOT = "/home/rinne/temp_survey"

TARGET_KEYWORDS = [
    "รัฐธรรมนูญ",
    "พระราชบัญญัติ",
    "พระราชกำหนด",
    "พระราชกฤษฎีกา",
    "กฎกระทรวง"
]

report_lock = Lock()
results = {kw: 0 for kw in TARGET_KEYWORDS}
results["others_skipped"] = 0
results["total_high_value_pages"] = 0 # To estimate cost later
detailed_list = [] # List of high-value files found

class LawScanner:
    def ocr_page_one(self, file_path):
        try:
            from google.cloud import vision
            from pdf2image import convert_from_path
            import io
            client = vision.ImageAnnotatorClient()
            images = convert_from_path(file_path, last_page=1)
            if not images: return ""
            img_byte_arr = io.BytesIO()
            images[0].save(img_byte_arr, format='JPEG')
            response = client.document_text_detection(image=vision.Image(content=img_byte_arr.getvalue()))
            return response.text_annotations[0].description if response.text_annotations else ""
        except: return ""

    def scan_file(self, file_path, year):
        try:
            # 1. Fast text check
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            text = reader.pages[0].extract_text() or ""
            
            # 2. OCR if needed
            if len(text.strip()) < 10:
                text = self.ocr_page_one(file_path)

            found_cats = [kw for kw in TARGET_KEYWORDS if kw in text]
            
            with report_lock:
                if found_cats:
                    for cat in found_cats:
                        results[cat] += 1
                    results["total_high_value_pages"] += num_pages
                    detailed_list.append({
                        "year": year,
                        "file": os.path.basename(file_path),
                        "categories": found_cats,
                        "pages": num_pages
                    })
                    return True
                else:
                    results["others_skipped"] += 1
        except: pass
        return False

def process_zip_survey(zip_path, executor, year):
    zip_name = os.path.basename(zip_path)
    temp_dir = os.path.join(TEMP_ROOT, zip_name.replace('.zip', ''))
    os.makedirs(temp_dir, exist_ok=True)
    
    subprocess.run(["unzip", "-o", "-q", zip_path, "-d", temp_dir], check=False)
    
    pdfs = []
    for root, _, files in os.walk(temp_dir):
        for f in files:
            if f.lower().endswith('.pdf'):
                pdfs.append(os.path.join(root, f))
    
    if pdfs:
        futures = [executor.submit(LawScanner().scan_file, p, year) for p in pdfs]
        for _ in concurrent.futures.as_completed(futures): pass
            
    shutil.rmtree(temp_dir)
    return len(pdfs)

def main():
    os.makedirs(TEMP_ROOT, exist_ok=True)
    all_zips = []
    for root, _, files in os.walk(ZIP_ROOT):
        for f in files:
            if f.lower().endswith('.zip'):
                year = os.path.basename(root)
                all_zips.append((os.path.join(root, f), year))
    
    all_zips.sort(key=lambda x: x[1], reverse=True)
    
    print(f"🔍 [SURVEY MODE] Scanning {len(all_zips)} Zips for High-Value Laws...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_ZIPS) as zip_exec:
        with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as pdf_exec:
            futures = [zip_exec.submit(process_zip_survey, zp[0], pdf_exec, zp[1]) for zp in all_zips]
            
            count = 0
            for future in concurrent.futures.as_completed(futures):
                count += 1
                if count % 10 == 0:
                    with report_lock:
                        # Periodic save of report
                        report_data = {"stats": results, "files": detailed_list}
                        with open(SURVEY_REPORT, 'w', encoding='utf-8') as f:
                            json.dump(report_data, f, ensure_ascii=False, indent=2)
                    print(f"📊 Surveyed {count}/{len(all_zips)} Zips... Found {len(detailed_list)} targets.")

    # Final Save
    report_data = {"stats": results, "files": detailed_list}
    with open(SURVEY_REPORT, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print("✅ Survey Complete! Report saved to", SURVEY_REPORT)

if __name__ == "__main__":
    main()
