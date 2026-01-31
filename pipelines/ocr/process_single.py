import os
import json
import pdfplumber
import datetime
from pythainlp import word_tokenize
from pythainlp.util import normalize

# --- Configuration ---
SOURCE_PDF = "downloads/2568/Deka_6267-2568_(Ref720024).pdf"
OUTPUT_DIR = "cleaned_output"
CUSTOM_DICT = {
    "ร่างกิจการบุคคล": "ราชกิจจานุเบกษา",
    "สภานั้น": "สถาบัน",
    "มีคุณยน": "มิถุนายน",
    "สัมผัส": "ล้มละลาย" 
    # Add more from word_fix_dictionary.json if needed
}

def clean_text_custom(text):
    # 1. Normalize (Remove duplicate spaces, zero-width chars)
    text = normalize(text)
    
    # 2. Apply Custom Dictionary
    for wrong, right in CUSTOM_DICT.items():
        text = text.replace(wrong, right)
        
    return text

def process_file():
    print(f"🚀 Processing File: {SOURCE_PDF}")
    
    # 1. Ensure Output Directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📂 Created Output Directory: {OUTPUT_DIR}")
        
    # 2. Extract Text
    full_text = ""
    with pdfplumber.open(SOURCE_PDF) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: full_text += t + "\n"
            
    print(f"✅ Text Extracted: {len(full_text)} chars")
    
    # 3. Clean Text
    cleaned_text = clean_text_custom(full_text)
    
    # 4. Tokenize (Demonstrate PyThaiNLP structure)
    tokens = word_tokenize(cleaned_text, engine="newmm")
    
    # 5. Save Result
    output_filename = os.path.basename(SOURCE_PDF).replace(".pdf", "_cleaned.json")
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    result = {
        "filename": os.path.basename(SOURCE_PDF),
        "processed_at": datetime.datetime.now().isoformat(),
        "original_length": len(full_text),
        "cleaned_length": len(cleaned_text),
        "raw_text": cleaned_text, # Saving the cleaned version
        "tokens_preview": tokens[:20] 
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    print(f"💾 Saved to: {output_path}")

if __name__ == "__main__":
    process_file()
