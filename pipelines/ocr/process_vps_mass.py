import os
import json
import glob
import pdfplumber
import datetime
from pythainlp import word_tokenize
from pythainlp.util import normalize
import re
from multiprocessing import Pool, cpu_count
import time

# --- Configuration ---
# ใช้ "." (จุด) หมายถึง Folder ปัจจุบันที่วาง Script อยู่
BASE_DIR = os.getcwd() 
SOURCE_DIR = os.path.join(BASE_DIR, "downloads") 
OUTPUT_DIR = os.path.join(BASE_DIR, "cleaned_output")

# จำนวน Core ที่ต้องการใช้ (ใส่เลข 8 ตาม Spec หรือให้มันหาเอง)
# ถ้าอยากปรับลดก็เปลี่ยนเลขนี้ครับ เช่น 4 หรือ 6
NUM_WORKERS = 5 # Adjusted to 5 cores as requested

# Default fallback dictionary
CUSTOM_DICT = {
    "ร่างกิจการบุคคล": "ราชกิจจานุเบกษา",
    "สภานั้น": "สถาบัน",
    "มีคุณยน": "มิถุนายน",
    "สัมผัส": "ล้มละลาย" 
}

# Load External Dictionary if exists
DICT_PATH = os.path.join(BASE_DIR, "word_fix_dictionary.json")
if os.path.exists(DICT_PATH):
    try:
        with open(DICT_PATH, 'r', encoding='utf-8') as f:
            external_dict = json.load(f)
            # Support both { "key": "val" } and { "dict": { "key": "val" } } formats
            if "dict" in external_dict:
                CUSTOM_DICT.update(external_dict["dict"])
            else:
                CUSTOM_DICT.update(external_dict)
        print(f"📚 Loaded {len(CUSTOM_DICT)} words from custom dictionary.")
    except Exception as e:
        print(f"⚠️ Failed to load dictionary: {e}")
else:
    print("⚠️ Custom dictionary file not found, using minimal fallback.")

def clean_text_custom(text):
    if not text: return ""
    text = normalize_legacy_thai(text)
    text = fix_tone_sequence(text)
    text = normalize(text)
    for wrong, right in CUSTOM_DICT.items():
        text = text.replace(wrong, right)
    return text

def normalize_legacy_thai(text):
    if not text: return ""
    pua_map = {
        "\uf70a": "\u0e48", "\uf70b": "\u0e49", "\uf70c": "\u0e4a", "\uf70d": "\u0e4b",
        "\uf70e": "\u0e4c", "\uf700": "\u0e10", "\uf70f": "\u0e0d"
    }
    for pua, std in pua_map.items():
        text = text.replace(pua, std)
    return text

def fix_tone_sequence(text):
    thai_consonants = r"[\u0e01-\u0e2e]"
    thai_upper_vowels = r"[\u0e31\u0e34-\u0e3a\u0e47]" 
    thai_tones = r"[\u0e48-\u0e4b]"
    pattern = re.compile(f"({thai_consonants})({thai_upper_vowels})({thai_consonants})({thai_tones})")
    return pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}{m.group(4)}{m.group(3)}", text)

def extract_metadata_robust(text):
    data = {}
    
    # 1. Case No
    match_no = re.search(r"คำพิพากษาศาลฎีกาที่\s*(\d+/\d+)", text)
    if not match_no: match_no = re.search(r"^(\d+/\d+)", text, re.MULTILINE)
    if match_no:
        data['case_no_full'] = match_no.group(1)
        data['case_no_short'] = match_no.group(1).split('/')[0]
    
    # 2. Plaintiff
    match_plaintiff = re.search(r"(?:คำพิพากษาศาลฎีกาที่.*?\n)?(.*?)\s+(?:โจทก์|โจทย์)", text, re.DOTALL)
    if match_plaintiff:
        raw = match_plaintiff.group(1).strip()
        lines = [l.strip() for l in raw.split('\n') if l.strip()]
        if lines:
            candidate = lines[-1]
            candidate = re.sub(r"(คำพิพากษาศาลฎีกาที่|คำสั่งคำร้องที่)\s*", "", candidate).strip()
            candidate = re.sub(r"^[\d/]+\s+", "", candidate).strip()
            if candidate and "2466" not in candidate:
                 data['plaintiff'] = candidate
            elif len(lines) > 1:
                 data['plaintiff'] = lines[-2]

    # 3. Defendant
    match_defendant = re.search(r"(?:โจทก์|โจทย์)\s+(.*?)\s+(?:จำเลย|ล\s*\n)", text[:800], re.DOTALL)
    if match_defendant:
        raw = match_defendant.group(1).strip()
        lines = [l.strip() for l in raw.split('\n') if l.strip()]
        if lines: data['defendant'] = lines[-1]

    # 4. Laws
    laws = set()
    text_fixed = re.sub(r"ป\s+วิ\s+พ", "ป.วิ.พ.", text)
    text_fixed = re.sub(r"ป\s+อ", "ป.อ.", text_fixed)
    matches_section = re.findall(r"มาตรา\s*([\d๓-๙]+)", text_fixed)
    for m in matches_section: laws.add(f"มาตรา {m}")
    for m in re.findall(r"(พระราชบัญญัติ[^\s]+|พ\.ร\.บ\.[^\s]+)", text_fixed): laws.add(m)
    for m in re.findall(r"(ป\.[^\s]+)", text_fixed): laws.add(m)
    data['laws_found'] = list(laws)

    # 5. Court
    match_court = re.search(r"คำพิพากษา(ศาล[^\s]+)", text)
    if match_court: data['court_type'] = match_court.group(1).replace("ที่", "").strip()

    # 6. Outcome
    keywords = {
        "พิพากษายืน": "Affirmed (ยืน)", "พิพากษากลับ": "Reversed (กลับ)",
        "พิพากษาแก้": "Amended (แก้)", "ยกฟ้อง": "Dismissed (ยกฟ้อง)",
        "ยกคำร้อง": "Dismissed (ยกคำร้อง)", "อนุญาตให้ถอน": "Withdrawn (ถอน)", "ให้ขับไล่": "Eviction (ขับไล่)"
    }
    outcomes = []
    text_end = text[-1000:]
    for kw, label in keywords.items():
        if kw in text_end: outcomes.append(label)
    if not outcomes:
        for kw, label in keywords.items():
            if kw in text: outcomes.append(label)
    if outcomes: data['outcome'] = list(set(outcomes))

    return data

def process_single_file(pdf_path):
    """Worker function for multiprocessing"""
    try:
        # Check if output already exists (Skip optimization)
        output_filename = os.path.basename(pdf_path).replace(".pdf", "_cleaned.json")
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # Uncomment to skip existing
        # if os.path.exists(output_path): return f"Skipped: {output_filename}"

        full_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t: full_text += t + "\n"
        
        if not full_text.strip(): return f"Empty: {output_filename}"

        cleaned_text = clean_text_custom(full_text)
        tokens = word_tokenize(cleaned_text, engine="newmm")
        meta = extract_metadata_robust(cleaned_text)

        result = {
            "filename": os.path.basename(pdf_path),
            "processed_at": datetime.datetime.now().isoformat(),
            "metadata": {
                "source_path": pdf_path,
                "token_count": len(tokens),
                "extraction_data": meta
            },
            "raw_text": cleaned_text
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        return f"{os.path.basename(pdf_path)}|Success"
            
    except Exception as e:
        return f"{os.path.basename(pdf_path)}|Error: {e}"

def main():
    print(f"🚀 Batch Processing Directory: {SOURCE_DIR}")
    print(f"⚡ CPU Cores Detected: {cpu_count()} | Using Workers: {NUM_WORKERS}")
    
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
        
    print("🔍 Scanning PDF files...")
    # Recursive search
    pdf_files = glob.glob(os.path.join(SOURCE_DIR, "**", "*.pdf"), recursive=True)
    # Also support current dir recursive if running adjacent
    if not pdf_files:
         pdf_files = glob.glob("downloads/**/*.pdf", recursive=True)
         
    total_files = len(pdf_files)
    print(f"🎯 Found {total_files} PDF(s) to process")
    
    start_time = time.time()
    
    # Multiprocessing Pool
    with Pool(processes=NUM_WORKERS) as pool:
        # Create an iterator
        for i, result in enumerate(pool.imap_unordered(process_single_file, pdf_files), 1):
            fname, status = result.split("|", 1)
            # Simple log to stdout (can be viewed in nohup.out)
            if i % 20 == 0: # Log every 20 files to see movement
                elapsed = time.time() - start_time
                rate = i / elapsed
                print(f"✅ [{i}/{total_files}] {fname} -> {status} (Speed: {rate:.2f}/s)")

    print(f"\n🏁 Complete. Processed {total_files} files in {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
