import google.generativeai as genai
import google.api_core.exceptions
import os
import json
import glob
import time
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import logging
from collections import deque

# --- CONFIGURATION ---
API_KEY = "AIzaSyB6t5VFdMSX-rMMVQ7rmvpe_dxqNHIIamA"
MODEL_NAME = "gemini-2.0-flash" 
OCR_ROOT = "/mnt/data/downloads/ocr/iapp"
OUTPUT_FILE = "/home/rinne/law_knowledge_graph_final.jsonl"
PROGRESS_FILE = "/home/rinne/kg_progress_log.txt"
FAILED_LOG = "/home/rinne/kg_failed_log.txt"

MAX_WORKERS = 50 
TARGET_KEYWORDS = [
    "คำพิพากษาศาลฎีกา", "คำสั่งศาล", "ศาลฎีกา", # Judicial
    "พระราชบัญญัติ", "พระราชกฤษฎีกา", "กฎกระทรวง", "ประกาศ" # Legislative/Executive
]

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
                    handlers=[logging.FileHandler("kg_pipeline.log"), logging.StreamHandler()])

# --- STATE ---
processed_ids = set()
file_lock = threading.Lock()
genai.configure(api_key=API_KEY)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            for line in f:
                processed_ids.add(line.strip())

def save_progress(doc_id):
    with file_lock:
        with open(PROGRESS_FILE, 'a') as f:
            f.write(f"{doc_id}\n")

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

def process_document(doc_json):
    """Process a single document JSON object (or list of objects)."""
    if not doc_json: return
    
    # Handle case where JSONL line is a LIST of docs, not a single doc
    if isinstance(doc_json, list):
        for item in doc_json:
            process_document(item)
        return

    if not isinstance(doc_json, dict):
        logging.warning(f"Skipping non-dict record: {type(doc_json)}")
        return
    
    # 1. Identity
    pdf_file = doc_json.get('pdf_file')
    if not pdf_file or not isinstance(pdf_file, str):
        # Check if 'file_name' exists instead? or generate random
        pdf_file = f"unknown_{time.time()}.pdf"
        
    if pdf_file in processed_ids: return

    # 2. Extract Text
    # Utilize get_all_strings to be structure-agnostic
    data_content = doc_json.get('data') 
    # data_content could be None, Dict, List, String...
    
    all_text_list = get_all_strings(data_content)
    full_text = "\n".join(all_text_list)
    
    # 3. Filter (Fast Check)
    if len(full_text) < 50: return # Too short
    
    is_target = False
    for kw in TARGET_KEYWORDS:
        if kw in full_text[:4000]: # Check header/intro
            is_target = True
            break
            
    if not is_target:
        return # Skip non-relevant docs to save cost

    # 4. AI Generation
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Truncate to avoid context limit (if PDF is huge)
        # Gemini 2.0 Flash has 1M context, so 30-50 pages text is fine.
        # But we limit to ~100k chars to be safe/fast/cheap.
        input_text = full_text[:100000] 
        
        prompt = f"""
        Analyze this Thai legal document text and extract a Knowledge Graph in JSON.
        
        Schema:
        {{
          "file_name": "{pdf_file}",
          "document_meta": {{
              "doc_type": "Type (Act, Decree, Judgment, Order, Announce)",
              "title": "Full Official Title",
              "case_number": "Red/Black Number (if judgment)",
              "issue_date": "YYYY-MM-DD or Text",
              "gazette_ref": "Volume/Page (if found)"
          }},
          "summary": "Brief summary of the essence (Thai)",
          "entities": {{
              "organizations": ["List of orgs"],
              "persons": ["List of people"],
              "locations": ["List of locations"]
          }},
          "legal_provisions": [
              {{ "section": "Section No", "text": "Content snippet" }}
          ],
          "relations": {{
              "cancels": ["Other laws cancelled"],
              "amends": ["Other laws amended"],
              "refers_to": ["Other laws mentioned"]
          }}
        }}
        
        Input Text:
        {input_text}
        """

        response = model.generate_content(prompt)
        
        # 5. Save Result
        result = json.loads(response.text)
        
        # FIX: Sometimes Gemini returns a LIST like [{...}] instead of {...}
        if isinstance(result, list):
            if len(result) > 0:
                result = result[0]
            else:
                result = {} # Empty list?

        # Enforce filename in output
        result['file_name'] = pdf_file 
        result['raw_text_snippet'] = full_text[:100] # Debug snippet
        
        # --- VERTEX AI FORMAT ADAPTER (Native) ---
        # 1. ID Cleaning: Remove .pdf and dots
        clean_id = pdf_file.replace('.pdf', '').replace('.', '_')
        
        # 2. Wrap in structData
        vertex_record = {
            "id": clean_id,
            "structData": result
        }

        # 6. Append to Output File (Thread Safe)
        with output_lock:
            with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(vertex_record, ensure_ascii=False) + '\n')
        
        save_progress(pdf_file)
        logging.info(f"✅ Indexed: {pdf_file} ({result['document_meta']['doc_type']})")
        # Minimal delay to keep flow smooth but fast (Full Speed Mode)
        time.sleep(0.1)

    except Exception as e:
        import traceback
        logging.error(f"❌ Failed {pdf_file}: {traceback.format_exc()}")
        with file_lock:
           with open(FAILED_LOG, 'a') as f: f.write(f"{pdf_file}|{str(e)}\n")

def worker_task(file_path):
    """Process a .jsonl file line by line."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    doc = json.loads(line)
                    process_document(doc)
                except Exception as e:
                    import traceback
                    error_msg = traceback.format_exc()
                    logging.error(f"JSON Line Error: {error_msg}")
                    # Also log to failed file with traceback snippet
                    with file_lock:
                        with open(FAILED_LOG, 'a') as f: 
                            f.write(f"LINE_ERROR|{str(e)}\n")
    except Exception as e:
        logging.error(f"File Error {file_path}: {e}")

def main():
    load_progress()
    
    # List all JSONL files
    all_jsonl = glob.glob(os.path.join(OCR_ROOT, "**/*.jsonl"), recursive=True)
    logging.info(f"🚀 Starting KG Pipeline on {len(all_jsonl)} JSONL files...")
    
    # We parallelize at FILE level (each worker takes one .jsonl and processes lines sequentially)
    # This prevents reading the same huge .jsonl into memory multiple times.
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(worker_task, f) for f in all_jsonl]
        for _ in concurrent.futures.as_completed(futures):
            pass

if __name__ == "__main__":
    main()
