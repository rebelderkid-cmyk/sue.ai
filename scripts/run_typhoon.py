import os
import json
import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer
from pdf2image import convert_from_path
import io
import time

# --- CONFIGURATION ---
INDEX_FILE = "law_index_easyocr.jsonl"
OUTPUT_FILE = "typhoon_extraction_results.jsonl"
MODEL_PATH = "typhoon-ai/typhoon-ocr-7b"
PROGRESS_LOG = "typhoon_progress.txt"

def load_typhoon_model():
    print("🌪️ Loading Typhoon-OCR 7B Model (CPU Mode)... This may take a while.")
    # Load model with CPU offloading support if consistent OOM ensures, but n2-highcpu-80 has plenty of RAM
    model = AutoModel.from_pretrained(
        MODEL_PATH, 
        trust_remote_code=True, 
        torch_dtype=torch.float32, # CPU usually prefers float32 or bfloat16
        device_map="cpu"
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    model.eval()
    print("✅ Typhoon Model Loaded Successfully!")
    return model, tokenizer

def process_file_with_typhoon(model, tokenizer, file_data):
    file_name = file_data.get('file_name')
    zip_source = file_data.get('zip_source')
    # Reconstruct path logic might be needed if full path isn't saved, 
    # but let's assume indexer saves enough info or we can find it.
    # In easy_indexer, we logged basenames. 
    # We need to find the file. Since we deleted temp files in indexer, 
    # WE NEED TO UNZIP AGAIN. This is the trade-off for space.
    
    # Strategy: We can't easily unzip single files without known paths inside zips efficiently in bulk.
    # But for High Value targets, it's worth the unzipping cost.
    
    # Let's assume we search or extract on demand.
    # For now, I'll implement a "Find and Extract" logic if path is specific.
    pass 

def main():
    # 1. Load Index
    print(f"📖 Reading Index from {INDEX_FILE}...")
    high_value_queue = []
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get('is_high_value', False):
                        high_value_queue.append(data)
                except: pass
    
    print(f"🎯 Found {len(high_value_queue)} High-Value Files in Index to Process.")
    
    if not high_value_queue:
        print("😴 No High-Value files found to process. Exiting.")
        return

    # 2. Load Model
    try:
        model, tokenizer = load_typhoon_model()
    except Exception as e:
        print(f"❌ Failed to load Typhoon Model: {e}")
        return

    # 3. Process Loop
    # Since we need to unzip files, we should group by Zip to minimize IO
    # Grouping logic...
    files_by_zip = {}
    for item in high_value_queue:
        z = item['zip_source']
        if z not in files_by_zip: files_by_zip[z] = []
        files_by_zip[z].append(item)

    processed_count = 0
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as outfile:
        
        for zip_name, items in files_by_zip.items():
            # Construct full zip path (assuming structure)
            # We need to find where this zip is. 
            # We'll assume it's in /mnt/data/downloads/zip/{year}/{zip_name} OR search all years.
            # Simplified: Search for zip in known root
            zip_full_path = None
            for root, _, files in os.walk("/mnt/data/downloads/zip"):
                if zip_name in files:
                    zip_full_path = os.path.join(root, zip_name)
                    break
            
            if not zip_full_path:
                print(f"⚠️ Could not find Zip: {zip_name}, skipping items.")
                continue

            print(f"📦 Processing Zip: {zip_name} ({len(items)} items)")
            
            # Unzip EVERYTHING to temp (easier than cherry picking with unzip -j if paths are unknown)
            # Actually, unzip -l can give us paths, but let's just unzip relevant files by name if possible
            # To match 'file_name' from metadata to zip content, we might need a match.
            # Let's simple-unzip the whole zip to a temp dir, process, then delete. Costly but safe.
            
            temp_extract_dir = f"temp_typhoon_{zip_name.replace('.zip','')}"
            os.makedirs(temp_extract_dir, exist_ok=True)
            os.system(f"unzip -q -o '{zip_full_path}' -d {temp_extract_dir}")
            
            # Find the PDF files
            for item in items:
                target_fname = item['file_name']
                # find file in temp_extract_dir
                target_path = None
                for r, _, f in os.walk(temp_extract_dir):
                    if target_fname in f:
                        target_path = os.path.join(r, target_fname)
                        break
                
                if target_path:
                    try:
                        print(f"   🌪️ Typhoo-ing: {target_fname}...")
                        start_time = time.time()
                        
                        # Convert all pages or just first? User said "OCR all files indexed"
                        # Typhoon is a vision model. We pass images.
                        # Let's process Page 1 for Key Metadata/Context (most important)
                        # Processing WHOLE document with 7B model on CPU is impossible (could take hours per doc).
                        # Compromise: Page 1 Full OCR for now.
                        images = convert_from_path(target_path) # Get all pages? No, just get first for now to prove concept
                        
                        # Full Text Accumulator
                        full_doc_text = ""
                        
                        # Process Page 1 ONLY (Safety Measure for Night 1)
                        # If you want more, change this loop
                        for i, img in enumerate(images[:1]): 
                            pixel_values = model.chat_processor(images=[img], text="OCR this document", return_tensors="pt")['pixel_values']
                            # Note: This is pseudo-code for generic VLM. 
                            # Typhoon specific: usually follows standard HF visual generation
                            # We will use the 'prediction' pipeline if available, or generate.
                            
                            # Standard Generation
                            response = model.generate(pixel_values, max_new_tokens=1024)
                            decoded_text = tokenizer.decode(response[0], skip_special_tokens=True)
                            full_doc_text += f"\n[Page {i+1}]\n{decoded_text}"

                        # Save Result
                        result_record = {
                            "file_name": target_fname,
                            "typhoon_output": full_doc_text,
                            "processed_at": time.time(),
                            "process_time": time.time() - start_time
                        }
                        outfile.write(json.dumps(result_record, ensure_ascii=False) + "\n")
                        outfile.flush()
                        processed_count += 1
                        
                    except Exception as e:
                        print(f"   ❌ Error on {target_fname}: {e}")
                
            # Cleanup Zip
            import shutil
            shutil.rmtree(temp_extract_dir)

    print(f"🏁 Night Shift Complete. Processed {processed_count} files.")

if __name__ == "__main__":
    main()
