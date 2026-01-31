import os
import json
import glob
import pdfplumber
import datetime
from pythainlp import word_tokenize
from pythainlp.util import normalize

# --- Configuration ---
SOURCE_DIR = "downloads/2568"
OUTPUT_DIR = "cleaned_output"
CUSTOM_DICT = {
    "ร่างกิจการบุคคล": "ราชกิจจานุเบกษา",
    "สภานั้น": "สถาบัน",
    "มีคุณยน": "มิถุนายน",
    "สัมผัส": "ล้มละลาย" 
    # Add more from word_fix_dictionary.json if needed
}

def clean_text_custom(text):
    if not text: return ""
    # 1. Normalize (Remove duplicate spaces, zero-width chars)
    text = normalize(text)
    
    # 2. Apply Custom Dictionary


def normalize_legacy_thai(text):
    """
    Fixes legacy MacThai/Win-874 PUA characters commonly found in old PDFs.
    """
    if not text: return ""
    
    # Map PUA to Standard Thai (Based on inspection)
    pua_map = {
        "\uf70a": "\u0e48", # Mai Ek
        "\uf70b": "\u0e49", # Mai Tho
        "\uf70c": "\u0e4a", # Mai Tri
        "\uf70d": "\u0e4b", # Mai Chattawa
        "\uf70e": "\u0e4c", # Thanthakhat
        "\uf700": "\u0e10", # Tho Than (Common artifact)
        "\uf70f": "\u0e0d", # Yor Ying (Bottom cut)
    }
    
    for pua, std in pua_map.items():
        text = text.replace(pua, std)
        
    for pua, std in pua_map.items():
        text = text.replace(pua, std)
        
    return text

def fix_tone_sequence(text):
    """
    Fixes displaced tone marks that appear after the final consonant.
    Pattern: [Consonant] [UpperVowel] [Consonant] [Tone] -> Swap Tone back
    Example: ขึน้ (ข+ึ+น+้) -> ขึ้น (ข+ึ+้+น)
             ชัน้ (ช+ั+น+้) -> ชั้น (ช+ั+้+น)
    """
    import re
    
    # 1. Define sets
    thai_consonants = r"[\u0e01-\u0e2e]"
    # Upper/Lower vowels that attach to the first consonant
    # \u0e31 (Mai Han-Akat), \u0e34-\u0e3a (Upper Vowels), \u0e47 (Mai Tai Khu)
    thai_upper_vowels = r"[\u0e31\u0e34-\u0e3a\u0e47]" 
    # Tones: \u0e48-\u0e4b
    thai_tones = r"[\u0e48-\u0e4b]"
    
    # Pattern: (C1)(V1)(C2)(Tone) -> Swap to (C1)(V1)(Tone)(C2)
    # Note: We must be careful not to swap if C2 is actually the start of a new syllable?
    # But usually a Tone cannot follow a final consonant in valid Thai spelling unless it belongs to the previous stack.
    # Exception: "ห" leading? "หน้" -> "หน้า" ? No, that's C+C+Tone.
    # The error specifically involves an Upper Vowel being visually present.
    
    pattern = re.compile(f"({thai_consonants})({thai_upper_vowels})({thai_consonants})({thai_tones})")
    
    def repl(m):
        c1, v1, c2, t = m.groups()
        return f"{c1}{v1}{t}{c2}" # Swap: C1 V1 T C2
        
    text = pattern.sub(repl, text)
    
    # Pattern 2: (C1)(C2)(Tone) where tone should be on C1?
    # Ex: หนา้ -> หน้า (H+N+MaiTho+SraA)
    # But the user specifically mentioned "ขึน้" "ชัน้" which have vowels.
    # Let's stick to the Vowel case first to be safe.
    
    return text

def clean_text_custom(text):
    if not text: return ""
    
    # 0. Fix Legacy Encoding First (PUA -> Std)
    text = normalize_legacy_thai(text)
    
    # 1. Fix Tone Position (New step)
    text = fix_tone_sequence(text)
    
    # 2. Normalize (Standard PyThaiNLP)
    text = normalize(text)
    
    # 3. Apply Custom Dictionary
    for wrong, right in CUSTOM_DICT.items():
        text = text.replace(wrong, right)
        
    return text

def extract_metadata_robust(text):
    """Robust extraction logic (imported from Phase2)"""
    data = {}
    import re
    
    # 1. Case No (เลขฎีกา)
    # Standard: "คำพิพากษาศาลฎีกาที่ 123/2566"
    match_no = re.search(r"คำพิพากษาศาลฎีกาที่\s*(\d+/\d+)", text)
    if not match_no:
        # Ancient: "27/2466" on a newline before the header
        match_no = re.search(r"^(\d+/\d+)", text, re.MULTILINE)
        
    if match_no:
        data['case_no_full'] = match_no.group(1)
        data['case_no_short'] = match_no.group(1).split('/')[0]
    
    # 2. Plaintiff (โจทก์) - IMPROVED
    # Archaic spelling: "โจทย์" (Yor Yuk) vs "โจทก์" (Gor Gai)
    # Pattern: "... [Plaintiff] โจทก์" or "... [Plaintiff] โจทย์"
    match_plaintiff = re.search(r"(?:คำพิพากษาศาลฎีกาที่.*?\n)?(.*?)\s+(?:โจทก์|โจทย์)", text, re.DOTALL)
    if match_plaintiff:
        raw = match_plaintiff.group(1).strip()
        lines = [l.strip() for l in raw.split('\n') if l.strip()]
        if lines:
            # Heuristic: Take the last line
            candidate = lines[-1]
            
            # Cleaning: Remove Header Prefixes
            candidate = re.sub(r"(คำพิพากษาศาลฎีกาที่|คำสั่งคำร้องที่)\s*", "", candidate).strip()
            
            # Cleaning: Remove leading Case No (e.g. "6267/2568 Plaintiff")
            candidate = re.sub(r"^[\d/]+\s+", "", candidate).strip()
            
            if candidate and "2466" not in candidate:
                 data['plaintiff'] = candidate
            elif len(lines) > 1:
                 # Fallback to previous line if current is just metadata/date
                 data['plaintiff'] = lines[-2]
            
    # 3. Defendant (จำเลย)
    # Archaic: sometimes "จำเลย" is missing or abbreviated.
    # Pattern: "โจทก์ ... [Defendant] จำเลย"
    # Limit search to first 500 chars to avoid body text
    header_text = text[:800] 
    match_defendant = re.search(r"(?:โจทก์|โจทย์)\s+(.*?)\s+(?:จำเลย|ล\s*\n)", header_text, re.DOTALL)
    if match_defendant:
        raw = match_defendant.group(1).strip()
        lines = [l.strip() for l in raw.split('\n') if l.strip()]
        if lines:
             data['defendant'] = lines[-1]
        
    # 4. Laws Involved (กฎหมายที่เกี่ยวข้อง) - IMPROVED
    laws = set()
    
    # Fix spaced abbreviations first
    text_fixed = re.sub(r"ป\s+วิ\s+พ", "ป.วิ.พ.", text)
    text_fixed = re.sub(r"ป\s+อ", "ป.อ.", text_fixed)
    
    # Support Thai Numerals in Sections (e.g., มาตรา ๓๓๖)
    matches_section = re.findall(r"มาตรา\s*([\d๓-๙]+)", text_fixed)
    for m in matches_section: laws.add(f"มาตรา {m}")
        
    matches_act = re.findall(r"(พระราชบัญญัติ[^\s]+|พ\.ร\.บ\.[^\s]+)", text_fixed)
    for m in matches_act: laws.add(m)
        
    matches_code = re.findall(r"(ป\.[^\s]+)", text_fixed)
    for m in matches_code: laws.add(m)
        
    data['laws_found'] = list(laws)
    
    # 5. Court Type (ศาล)
    match_court = re.search(r"คำพิพากษา(ศาล[^\s]+)", text)
    if match_court:
        data['court_type'] = match_court.group(1).replace("ที่", "").strip()

    # 6. Outcome (ผลคำพิพากษา) - NEW
    # Look for keywords indicating the final result
    outcomes = []
    text_last_part = text[-1000:] # Focus on the end of the document
    
    keywords = {
        "พิพากษายืน": "Affirmed (ยืน)",
        "พิพากษากลับ": "Reversed (กลับ)",
        "พิพากษาแก้": "Amended (แก้)",
        "ยกฟ้อง": "Dismissed (ยกฟ้อง)",
        "ยกคำร้อง": "Dismissed (ยกคำร้อง)",
        "อนุญาตให้ถอน": "Withdrawn (ถอน)",
        "ให้ขับไล่": "Eviction (ขับไล่)" # Seen in ancient deka
    }
    
    for kw, label in keywords.items():
        if kw in text_last_part:
            outcomes.append(label)
            
    if outcomes:
        data['outcome'] = outcomes
    else:
        # Fallback: check whole text if not found at end (sometimes ancient docs are short)
        for kw, label in keywords.items():
            if kw in text:
                outcomes.append(label)
        if outcomes: data['outcome'] = list(set(outcomes))

    return data

def process_batch():
    print(f"🚀 Batch Processing Directory: {SOURCE_DIR}")
    
    # 1. Ensure Output Directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📂 Created Output Directory: {OUTPUT_DIR}")
        
    # 2. Find Files (Recursive)
    pdf_files = []
    
    # Search in downloads (recursive)
    pdf_files.extend(glob.glob("downloads/**/*.pdf", recursive=True))
    
    # Search in TestFix (recursive)
    pdf_files.extend(glob.glob("TestFix/**/*.pdf", recursive=True))
    
    # Filter out hidden files or dupes
    pdf_files = sorted(list(set(pdf_files)))
    
    print(f"🎯 Found {len(pdf_files)} PDF(s) to process")
    
    for pdf_path in pdf_files:
        print(f"\n📄 Processing: {os.path.basename(pdf_path)}")
        
        # 3. Extract Text
        full_text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t: full_text += t + "\n"
        except Exception as e:
            print(f"❌ Error extracting text: {e}")
            continue
            
        if not full_text.strip():
            print("⚠️  Warning: No text extracted (possibly scanned image or CID issue)")
            
        print(f"✅ Text Extracted: {len(full_text)} chars")
        
        # 4. Clean Text
        cleaned_text = clean_text_custom(full_text)
        
        # 5. Tokenize
        tokens = word_tokenize(cleaned_text, engine="newmm")
        
        # 6. Extract Metadata
        meta = extract_metadata_robust(cleaned_text)

        # 7. Save Result
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

    print("\n🏁 Batch Processing Complete.")

if __name__ == "__main__":
    process_batch()
