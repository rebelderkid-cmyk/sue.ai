import json
import re
import sys

def check_anomalies(file_path):
    print("| PDF File | Page | Suspicious Text | Likely Correction | Pattern Type |")
    print("|---|---|---|---|---|")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            pdf_file = data.get('pdf_file', 'unknown')
            
            # Extract text from nested structure
            raw_text = ""
            inner_data = data.get('data', {})
            # Handle case where data might be None
            if inner_data:
                raw_results = inner_data.get('raw_results', [])
                for page in raw_results:
                    raw_text += page.get('raw_output', '') + " "
            
            # Fallback if raw_text is still empty (though less likely if structure matches)
            if not raw_text:
                 raw_text = data.get('raw_text', '')
            
            # Helper to print row
            def report(page, suspicious, correction, p_type):
                # Escape pipes in text
                susp = suspicious.replace('|', '\|').replace('\n', ' ')
                corr = correction.replace('|', '\|')
                print(f"| {pdf_file} | {page} | {susp} | {corr} | {p_type} |")

            # scans
            # 1. Gazette Header issues
            # "เฉลย์ ... ตอนพิเศษ" -> "เล่ม ... ตอนพิเศษ"
            if 'เฉลย์' in raw_text and 'ตอนพิเศษ' in raw_text:
                match = re.search(r'(เฉลย์.*?ตอนพิเศษ)', raw_text)
                if match:
                    report('Header', match.group(1), "เล่ม ... ตอนพิเศษ", "Header Corruption")
            
            # "ร่างกิจการบุคคล" -> "ราชกิจจานุเบกษา"
            if 'ร่างกิจการบุคคล' in raw_text:
                 report('Header', 'ร่างกิจการบุคคล', "ราชกิจจานุเบกษา", "Header Corruption")

            # 2. Month issues
            # มีคุณยน -> มิถุนายน
            if 'มีคุณยน' in raw_text:
                report('Content', 'มีคุณยน', 'มิถุนายน', 'Month Misspelling')
            
            # เดือนกรุณา -> เดือนกรกฎาคม
            if 'เดือนกรุณา' in raw_text:
                report('Content', 'เดือนกรุณา', 'เดือนกรกฎาคม', 'Month Misspelling')

            # รับความ -> ธันวาคม (often appears as เดือน...รับความ)
            match = re.search(r'เดือน.*?รับความ', raw_text)
            if match:
                report('Content', match.group(0), 'เดือน...ธันวาคม', 'Month Misspelling')

            # 3. Institution issues
            # สภานั้น -> สถาบัน
            if 'สภานั้น' in raw_text:
                report('Content', 'สภานั้น', 'สถาบัน', 'Common OCR Error')
                
            # 4. English Garbage
            if 'anggal' in raw_text:
                report('Footer', 'anggal', 'วันที่ (Date)', 'English Garbage')
            
            if 'ling' in raw_text and 'ลิง' in raw_text: 
                # "ลิง" often appears instead of valid date parts or mixed with english
                report('Footer', 'ลิง / ling', 'Year/Date part?', 'Garbage')

            # 5. Last word
            if 'สูตรท้าย' in raw_text:
                report('Content', 'สูตรท้าย', 'สุดท้าย', 'Common OCR Error')

            # 6. Specific date format error from sample
            # "ถ้วนสิ้นวัน" -> "ทุกสิ้นวัน" or similar?
            # "ค่านวม" -> "คำนวณ" (Calculate)
            if 'ค่านวม' in raw_text:
                 report('Content', 'ค่านวม', 'คำนวณ', 'Common OCR Error')
                 
            # "น้ำส่ง" -> "นำส่ง" (Remit/Deliver)
            if 'น้ำส่ง' in raw_text:
                report('Content', 'น้ำส่ง', 'นำส่ง', 'Common OCR Error')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_anomalies.py <jsonl_file>")
        sys.exit(1)
    
    check_anomalies(sys.argv[1])
