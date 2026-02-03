import os
import json
import google.generativeai as genai
from pdf2image import convert_from_bytes

# Configuration
PDF_PATH = "scrapers/ratchakitcha/downloads_poc/รัฐธรรมนูญแห่งราชอาณาจักรไทย พุทธศักราช ๒๔๗๕ แก้ไขเพิ่มเติม พุทธศักราช ๒๔๙๕.pdf"
API_KEY = os.environ.get("GEMINI_API_KEY")

def run_json_test():
    if not API_KEY:
        print("❌ Error: GEMINI_API_KEY not set.")
        return

    print(f"🚀 Processing PDF: {os.path.basename(PDF_PATH)}")
    
    # 1. Convert First 2 Pages to Images (Using Bytes to avoid Path Encoding Issues)
    print("📸 Converting PDF pages 1-2 to images...")
    try:
        with open(PDF_PATH, "rb") as f:
            pdf_bytes = f.read()
        images = convert_from_bytes(pdf_bytes, first_page=1, last_page=2)
    except Exception as e:
        print(f"❌ PDF Error: {e}")
        return
    
    # Resize for optimization
    processed_images = []
    for img in images:
        if img.width > 2000:
            img.thumbnail((2000, 2000))
        processed_images.append(img)

    # 2. Setup Gemini
    print("✨ Sending to Gemini 2.0 Flash (Mode: JSON Extraction)...")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

    # 3. Structured Prompt
    prompt = """
    Role: Senior Thai Legal Data Engineer.
    Task: Extract data from these Royal Gazette pages into valid JSON.
    
    Output Format (JSON):
    {
      "document_title": "Full Thai Title",
      "gazette_volume": "Volume No",
      "gazette_section": "Section No",
      "publication_date": "Thai Date String",
      "content": [
        {
          "section_id": "1", 
          "text": "Full text of section 1..."
        },
        {
          "section_id": "2",
          "text": "Full text of section 2..."
        }
      ]
    }
    
    Rules:
    - If a section has no number (like preamble), use section_id: "preamble".
    - Correct any obvious OCR errors in Thai text.
    - Output ONLY raw JSON (no markdown ```json blocks).
    """

    try:
        # Send Prompt + Images
        inputs = [prompt] + processed_images
        response = model.generate_content(inputs)
        
        # Clean response (sometimes Gemini adds ```json wrapper)
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        
        # Parse & Pretty Print
        data = json.loads(raw_text)
        print("\n=== 💎 GENERATED JSON ===\n")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("\n=========================\n")
        
        # Save
        with open("pipelines/ocr/test_output.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("💾 Saved to pipelines/ocr/test_output.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Print raw response for debugging if JSON parse fails
        if 'response' in locals():
            print("Raw Response:", response.text)

if __name__ == "__main__":
    run_json_test()
