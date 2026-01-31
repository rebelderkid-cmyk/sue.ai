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

# --- CONFIGURATION (TARGETED HIGH-VALUE MODE) ---
MAX_PDF_WORKERS = 100       # 100 Cores
CONCURRENT_ZIPS = 3         # Unzip 3 sets ahead
OUTPUT_FILE = "/home/rinne/royal_gazette_corpus_v1.jsonl"
PROGRESS_FILE = "/home/rinne/processed_zips_v1.txt"
TEMP_ROOT = "/home/rinne/temp_extract"
ZIP_ROOT = "/mnt/data/downloads/zip"

# Categories to keep (From User Image)
TARGET_KEYWORDS = [
    "รัฐธรรมนูญ",
    "พระราชบัญญัติ",
    "พระราชกำหนด",
    "พระราชกฤษฎีกา",
    "กฎกระทรวง"
]

progress_lock = Lock()
write_lock = Lock()

class LawDocumentExtractor:
    def __init__(self):
        self.section_pattern = r"(มาตรา\s*\d+(?:/\d+|(?:\s+(?:ทวิ|ตรี|จัตวา|เบญจ|ฉ|สัตต|อัฏฐ|นว|ทศ)))?)"
        
    def clean_text(self, text):
        if not text: return ""
        return "".join(c for c in text if ord(c) < 0x110000 and not (0xD800 <= ord(c) <= 0xDFFF))

    def is_high_value(self, text_sample):
        if not text_sample: return False
        return any(kw in text_sample for kw in TARGET_KEYWORDS)

    def ocr_with_vision(self, file_path, first_page_only=False):
        try:
            from google.cloud import vision
            from pdf2image import convert_from_path
            import io
            client = vision.ImageAnnotatorClient()
            # Convert PDF - if first_page_only is True, just get the first page to save time/cost
            images = convert_from_path(file_path, last_page=1 if first_page_only else None)
            ocr_text = ""
            for image in images:
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='JPEG')
                response = client.document_text_detection(image=vision.Image(content=img_byte_arr.getvalue()))
                if response.text_annotations:
                    ocr_text += response.text_annotations[0].description + "\n"
            return ocr_text
        except Exception:
            return ""

    def process_file(self, file_path):
        """Hybrid High-Value Extraction Strategy"""
        text_content = ""
        
        # 1. Try fast pypdf on first page for filtering
        try:
            reader = PdfReader(file_path)
            first_page_text = reader.pages[0].extract_text() or ""
        except:
            first_page_text = ""

        # 2. If pypdf failed or returned nothing, try OCRing just the FIRST page
        if not first_page_text:
            first_page_text = self.ocr_with_vision(file_path, first_page_only=True)

        # 3. Filtering Check
        if not self.is_high_value(first_page_text):
            return None # Skip useless documents (announcements, etc.)

        # 4. If High-Value, try to extract full text using pypdf first (Free)
        full_text = ""
        try:
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted: full_text += extracted + "\n"
        except:
            pass

        # 5. If pypdf full text is too short, use Vision OCR (Paid but Accurate)
        if len(full_text.strip()) < 200:
            full_text = self.ocr_with_vision(file_path, first_page_only=False)

        if not full_text.strip():
            return None

        # 6. Extract Metadata
        full_text = self.clean_text(full_text)
        data = {
            "source_file": os.path.basename(file_path),
            "category_detected": [kw for kw in TARGET_KEYWORDS if kw in first_page_text],
            "sections_found": sorted(list(set(re.findall(self.section_pattern, full_text)))),
            "full_text": full_text,
            "processed_at": datetime.now().isoformat()
        }
        return data

def process_single_pdf_task(pdf_path):
    try:
        extractor = LawDocumentExtractor()
        result = extractor.process_file(pdf_path)
        if result:
            with write_lock:
                with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
            return True
    except Exception:
        pass
    return False

def handle_zip_unit(zip_path, executor):
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
        futures = [executor.submit(process_single_pdf_task, p) for p in pdfs]
        for _ in concurrent.futures.as_completed(futures): pass
            
    shutil.rmtree(temp_dir)
    with progress_lock:
        with open(PROGRESS_FILE, 'a') as f: f.write(zip_path + "\n")
    return len(pdfs)

def main():
    os.makedirs(TEMP_ROOT, exist_ok=True)
    
    # ALL YEARS PROCESSING with filtering
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
                    all_zips.append(path)
    
    all_zips.sort(reverse=True)
    total = len(all_zips)
    print(f"💎 [ALL-YEARS HIGH-VALUE MODE] | Total: {total} zips remaining.")

    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_PDF_WORKERS) as pdf_executor:
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_ZIPS) as zip_executor:
            zip_futures = [zip_executor.submit(handle_zip_unit, zp, pdf_executor) for zp in all_zips]
            for future in concurrent.futures.as_completed(zip_futures): pass

if __name__ == "__main__":
    main()
