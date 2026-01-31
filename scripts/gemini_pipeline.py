import google.generativeai as genai
import google.api_core.exceptions
import os
import json
import time
import zipfile
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import logging
import signal
import sys

# --- CONFIGURATION ---
API_KEY = "AIzaSyB6t5VFdMSX-rMMVQ7rmvpe_dxqNHIIamA"
MODEL_NAME = "gemini-2.0-flash" 
ZIP_ROOT = "/mnt/data/downloads/zip"
OUTPUT_FILE = "/home/rinne/law_knowledge_graph.jsonl"
FAILED_LOG = "/home/rinne/failed_files.log"
PROGRESS_FILE = "/home/rinne/pipeline_progress.txt"

MAX_WORKERS = 50           # High concurrency for Pay-as-you-go
MAX_RETRIES = 3            # Retry failed uploads/generations
Request_RPM_Delay = 0.0    # No artificial delay (Turbo Mode)

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("gemini_pipeline.log"),
        logging.StreamHandler()
    ]
)

# --- GLOBAL STATE ---
processed_files = set()
file_lock = threading.Lock()
shutdown_event = threading.Event()

def load_progress():
    """Load list of already processed zip files to resume from."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            for line in f:
                processed_files.add(line.strip())
        logging.info(f"🔄 Resuming... Found {len(processed_files)} processed items.")

def save_progress(identifier):
    """Mark a file/zip as processed."""
    with file_lock:
        with open(PROGRESS_FILE, 'a') as f:
            f.write(f"{identifier}\n")

def write_result(data):
    """Thread-safe write to JSONL output."""
    with file_lock:
        with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

def log_failure(filename, reason):
    with file_lock:
        with open(FAILED_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{filename} | {reason}\n")

def process_pdf_content(pdf_bytes, filename, zip_name):
    """Uploads PDF content to Gemini and extracts Knowledge Graph."""
    
    # 1. Create a temporary file because Gemini SDK needs a path (Upload from memory not fully supported in simple SDK)
    temp_path = f"/tmp/{filename}_{threading.get_ident()}.pdf"
    
    try:
        with open(temp_path, "wb") as f:
            f.write(pdf_bytes)
        
        # 2. Upload to Gemini
        file_ref = None
        for attempt in range(MAX_RETRIES):
            try:
                file_ref = genai.upload_file(path=temp_path, display_name=filename)
                break
            except Exception as e:
                if attempt == MAX_RETRIES - 1: raise e
                time.sleep(2 * (attempt + 1))

        # 3. Wait for Processing
        while file_ref.state.name == "PROCESSING":
            time.sleep(1)
            file_ref = genai.get_file(file_ref.name)
        
        if file_ref.state.name == "FAILED":
            raise Exception("Gemini File Processing Failed")

        # 4. Generate Content (Knowledge Graph Extraction)
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config={"response_mime_type": "application/json"}
        )
        
        prompt = """
        Analyze this Thai legal document and extract a Knowledge Graph in JSON format.
        
        Required Schema:
        {
          "file_name": "Original Filename",
          "document_meta": {
              "doc_type": "Type (e.g., Act, Decree)",
              "title": "Full specific title",
              "issue_date": "YYYY-MM-DD or Text",
              "gazette_volume": "Volume No",
              "gazette_page": "Page No"
          },
          "content": {
              "summary": "Brief summary (Thai)",
              "full_text": "Complete OCR Text (Thai)"
          },
          "entities": {
              "organizations": ["List of orgs"],
              "persons": ["List of key people"],
              "locations": ["List of locations"]
          },
          "legal_provisions": [
              { "section": "Section No", "text": "Content" }
          ],
          "relations": {
              "cancels": ["Laws cancelled by this"],
              "amends": ["Laws amended by this"],
              "refers_to": ["Other laws mentioned"]
          }
        }
        """
        
        response = model.generate_content([file_ref, prompt])
        
        # 5. Parsing & Saving
        try:
            result_json = json.loads(response.text)
            result_json['origin_zip'] = zip_name
            result_json['file_name'] = filename # Ensure filename is correct
            write_result(result_json)
            logging.info(f"✅ Indexed: {filename}")
        except json.JSONDecodeError:
            logging.error(f"❌ JSON Error in {filename}: {response.text[:100]}")
            log_failure(filename, "JSON Decode Error")
            # Save raw text fallback?
        
        # 6. Cleanup Cloud File
        try:
            genai.delete_file(file_ref.name)
        except: pass

    except Exception as e:
        logging.error(f"❌ Failed {filename}: {e}")
        log_failure(filename, str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def worker_task(zip_path):
    """Process a single Zip file."""
    if zip_path in processed_files:
        return

    try:
        zip_name = os.path.basename(zip_path)
        with zipfile.ZipFile(zip_path, 'r') as z:
            pdf_files = [f for f in z.namelist() if f.lower().endswith('.pdf')]
            
            # Sub-pool for files within a zip (Optional, but keeping simple for now: Serial inside Zip, Parallel Zips)
            # Actually, better to Parallelize FILES, not ZIPs, to avoid extracting huge zips all at once.
            # But structure here is: We are Worker.
            
            for pdf_file in pdf_files:
                if shutdown_event.is_set(): break
                
                # Check if this specific PDF is already done? (Maybe too granular tracking, stick to Zip level for resume)
                # For now, we process all PDFs in the Zip.
                
                with z.open(pdf_file) as f:
                    pdf_bytes = f.read()
                    process_pdf_content(pdf_bytes, pdf_file, zip_name)
        
        save_progress(zip_path) # Mark Zip as done

    except Exception as e:
        logging.error(f"❌ Zip Error {zip_path}: {e}")

def main():
    genai.configure(api_key=API_KEY)
    load_progress()
    
    # Find all zips
    all_zips = []
    for root, dirs, files in os.walk(ZIP_ROOT):
        for file in files:
            if file.endswith(".zip"):
                full_path = os.path.join(root, file)
                if full_path not in processed_files:
                    all_zips.append(full_path)
    
    logging.info(f"🚀 Starting Gemini Pipeline on {len(all_zips)} Zip files with {MAX_WORKERS} workers.")
    
    # Execution Pool
    # We parallelize at ZIP level because opening/list zip is cheap.
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        try:
            futures = [executor.submit(worker_task, zp) for zp in all_zips]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Worker Exception: {e}")
        except KeyboardInterrupt:
            logging.warning("🛑 Stopping pipeline...")
            shutdown_event.set()
            executor.shutdown(wait=False)

if __name__ == "__main__":
    main()
