import os
import json
import pdfplumber
import datetime
from pythainlp import word_tokenize
from process_batch import clean_text_custom, extract_metadata_robust

# Target File
PDF_PATH = "TestFix/Deka_27-2466_(Ref257770).pdf"
OUTPUT_DIR = "cleaned_output"

def process_single_file(pdf_path):
    print(f"🚀 Processing Single File: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return

    # 1. Extract
    full_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t: full_text += t + "\n"
    except Exception as e:
        print(f"❌ Error extracting: {e}")
        return

    print(f"✅ Text Extracted: {len(full_text)} chars")
    
    # 2. Clean
    cleaned_text = clean_text_custom(full_text)
    
    # 3. Tokenize
    tokens = word_tokenize(cleaned_text, engine="newmm")
    
    # 4. Metadata
    meta = extract_metadata_robust(cleaned_text)
    
    # 5. Save
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    output_filename = os.path.basename(pdf_path).replace(".pdf", "_cleaned.json")
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    result = {
        "filename": os.path.basename(pdf_path),
        "processed_at": datetime.datetime.now().isoformat(),
        "original_length": len(full_text),
        "cleaned_length": len(cleaned_text),
        "metadata": {
            "source_path": pdf_path,
            "token_count": len(tokens),
            "extraction_data": meta
        },
        "raw_text": cleaned_text, 
        "tokens_preview": tokens[:20] 
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    print(f"💾 Saved to: {output_path}")

if __name__ == "__main__":
    process_single_file(PDF_PATH)
