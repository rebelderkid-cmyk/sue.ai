import os
import json
from collections import defaultdict
import glob

OCR_ROOT = "/mnt/data/downloads/ocr/iapp"

def audit_ocr_data():
    stats = defaultdict(int)
    years = set()
    total_records = 0
    
    print("🔎 Starting Audit of OCR JSONL files...")
    
    # Walk through all directories
    # Expected structure: /mnt/data/downloads/ocr/iapp/YYYY/YYYY-MM.jsonl
    jsonl_files = glob.glob(os.path.join(OCR_ROOT, "**/*.jsonl"), recursive=True)
    
    if not jsonl_files:
        print("❌ No JSONL files found!")
        return

    print(f"📂 Found {len(jsonl_files)} JSONL files.")
    
    for file_path in jsonl_files:
        try:
            filename = os.path.basename(file_path) # e.g., 2024-09.jsonl
            year = filename.split('-')[0] # 2024
            
            line_count = 0
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for _ in f:
                    line_count += 1
            
            stats[year] += line_count
            years.add(year)
            total_records += line_count
            
        except Exception as e:
            print(f"⚠️ Error reading {file_path}: {e}")

    print("\n📊 --- Audit Report ---")
    print(f"Total Valid Records (Indexed PDFs): {total_records:,}")
    print(f"Date Range: {min(years) if years else '?'} - {max(years) if years else '?'}")
    print("\n📅 Breakdown by Year:")
    
    # Sort years numerically
    sorted_years = sorted(list(years), key=lambda x: int(x) if x.isdigit() else 0)
    
    for y in sorted_years:
        print(f"   {y}: {stats[y]:,}")

if __name__ == "__main__":
    audit_ocr_data()
