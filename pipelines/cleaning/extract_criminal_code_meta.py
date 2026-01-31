import re
import pandas as pd
import json
import os
import sys
import gc
import concurrent.futures
from datetime import datetime

class CriminalCodeExtractor:
    """
    Miner class to extract 'Criminal Code' (ประมวลกฎหมายอาญา) data 
    from Royal Gazette documents for Knowledge Graph construction.
    """
    
    def __init__(self):
        # Regex patterns for identification
        self.criminal_code_pattern = r"ประมวลกฎหมายอาญา"
        
        # Regex for Knowledge Graph Keys (Section ID)
        # Captures: มาตรา 288, มาตรา 288/1, มาตรา 288 ทวิ
        # Stricter pattern to avoid grabbing next word like "ผู้ใด" (Person)
        self.section_pattern = r"(มาตรา\s*\d+(?:/\d+|(?:\s+(?:ทวิ|ตรี|จัตวา|เบญจ|ฉ|สัตต|อัฏฐ|นว|ทศ)))?)"
        
    def is_criminal_code(self, text):
        """Check if the document content or title relates to Criminal Code."""
        if not text:
            return False
        return bool(re.search(self.criminal_code_pattern, text))

    def extract_metadata(self, file_path, text_content, meta_json=None, force_keep=False):
        """
        Extracts structured data for the Graph Node.
        """
        data = {
            "source_file": os.path.basename(file_path),
            "is_criminal_code": False,
            "sections_found": [],
            "graph_node_id": None, # Will be the primary Section if applicable
            "full_text": text_content if text_content else ""
        }
        
        # 1. Verification
        if not self.is_criminal_code(text_content):
            if meta_json and self.is_criminal_code(meta_json.get('title', '')):
                pass # Title says it is, so we proceed
            elif not force_keep:
                return None # Not what we are looking for (unless forced)

        if self.is_criminal_code(text_content):
            data["is_criminal_code"] = True
        
        # 2. Graph Key Extraction (Section extraction)
        # A single document might contain multiple sections (e.g. an Amendment Act)
        # For the Graph, we might want to split them or list them.
        sections = re.findall(self.section_pattern, text_content)
        data["sections_found"] = sorted(list(set(sections))) # Distinct sections
        
        return data

    def process_file(self, file_path):
        """
        Reads PDF file and extracts metadata.
        Strategies:
        1. pypdf (Fast, Free) - text layer
        2. Google Vision API (Cost, Slower) - OCR fallback
        """
        # 1. Try pypdf first
        text_content = ""
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            # Read ALL pages
            for page in reader.pages: # Removed [:5] slice
                extracted = page.extract_text()
                if extracted:
                    text_content += extracted + "\n"
        except Exception:
            pass # Fallback to OCR

        # 2. Check if text is sufficient
        # If text is empty or very short (< 50 chars), it's likely an image scan.
        if len(text_content.strip()) < 50:
            print(f"📷 Image PDF detected: {os.path.basename(file_path)}. Triggering Vision OCR...")
            text_content = self.ocr_with_vision(file_path)

        return self.extract_metadata(file_path, text_content)

    def ocr_with_vision(self, file_path):
        """
        Uses Google Vision API to OCR the first few pages of the PDF.
        Requires: pip install google-cloud-vision pdf2image
        And system: apt-get install poppler-utils
        """
        try:
            from google.cloud import vision
            from pdf2image import convert_from_path
            import io

            client = vision.ImageAnnotatorClient()
            
            # Convert ALL pages to images
            images = convert_from_path(file_path)
            
            ocr_text = ""
            for i, image in enumerate(images):
                # Convert PIL image to bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='JPEG')
                content = img_byte_arr.getvalue()

                image_vision = vision.Image(content=content)
                response = client.text_detection(image=image_vision)
                
                if response.text_annotations:
                    # absolute index 0 is the full text
                    ocr_text += response.text_annotations[0].description + "\n"
            
            return ocr_text

        except Exception as e:
            print(f"⚠️ OCR Prototyping Error on {file_path}: {e}")
            return ""

# Worker Function (Must be top-level for ProcessPool)
def process_single_file_worker(input_args):
    """
    Worker process.
    args: (miner_kw, file_path, force_ocr)
    miner_kw: placeholder if we need to init miner inside (which is better for pickling)
    """
    try:
        # Re-instantiate miner inside process to avoid Pickling issues with gRPC objects
        # Or if miner is simple, pass it. But gRPC clients often can't be pickled.
        # Safest is to init miner here or use a global one if process-forked (Linux default)
        
        # In 'spawn' or 'forkserver', we definitely need new miner.
        # In 'fork' (Linux default), we might inherit. 
        # Safest: Init new Miner specific to this process.
        
        miner = CriminalCodeExtractor() 
        file_path, force_ocr = input_args
        
        basename = os.path.basename(file_path)
        
        text_content = ""
        data = None
        
        if force_ocr:
            text_content = miner.ocr_with_vision(file_path)
            data = miner.extract_metadata(file_path, text_content, force_keep=True)
        else:
            data = miner.process_file(file_path)
            
        return data  # Return dict back to main process
        
    except Exception as e:
        # print(f"❌ Error {file_path}: {e}")
        return None

def process_directory(input_dir, output_file, limit=None, force_ocr=False):
    print(f"📂 Scanning metadata... {input_dir}")
    files_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                files_files.append(os.path.join(root, file))
                
    # Validation / Resume
    processed_files = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f_existing:
                for line in f_existing:
                    try:
                        rec = json.loads(line)
                        processed_files.add(rec.get('source_file'))
                    except: pass
        except: pass
    print(f"✅ Found {len(processed_files)} processed. Skipping.")

    # Filter
    files_to_process = [f for f in files_files if os.path.basename(f) not in processed_files]
    
    if limit:
        files_to_process = files_to_process[:limit]
    
    total_files = len(files_to_process)
    print(f"🔥 Starting Multiprocessing on {total_files} files (Limit: {limit})...")

    # Serialize arguments
    # We pass tuples: (file_path, force_ocr)
    tasks = [(f, force_ocr) for f in files_to_process]
    
    completed_count = 0
    
    # WRITING in MAIN PROCESS ONLY
    with open(output_file, 'a', encoding='utf-8') as f_out:
        with concurrent.futures.ProcessPoolExecutor(max_workers=6) as executor:
            # Submit all
            futures = [executor.submit(process_single_file_worker, t) for t in tasks]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    data = future.result()
                    if data:
                        f_out.write(json.dumps(data, ensure_ascii=False) + "\n")
                        f_out.flush()
                        
                        completed_count += 1
                        if completed_count % 10 == 0:
                            print(f"🚀 Speed Processing {completed_count}/{total_files}...")
                except Exception as e:
                    print(f"Err: {e}")

    print(f"✅ Complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # CMD usage: python extract.py <input_dir> <output_file> [limit] [--force-ocr]
        input_dir = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "law_graph_nodes.jsonl"
        
        limit = None
        force_ocr = False
        
        # Parse args manually for flexibility
        for arg in sys.argv[3:]:
            if arg == "--force-ocr":
                force_ocr = True
            elif arg.isdigit():
                limit = int(arg)
        
        start_time = datetime.now()
        process_directory(input_dir, output_file, limit, force_ocr)
        end_time = datetime.now()
        print(f"⏱️ Time taken: {end_time - start_time}")
    else:
        # Test usage
        miner = CriminalCodeExtractor()
        # ... (keep dummy test if needed, or remove)
        print("Usage: python extract_criminal_code_meta.py <input_dir> <output_file> [limit]")
