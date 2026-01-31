import os
import sys
import time
import json
import io
from pdf2image import convert_from_path
from google.cloud import vision
import easyocr

def test_google_vision(image_content):
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_content)
    response = client.document_text_detection(image=image)
    if response.text_annotations:
        return response.text_annotations[0].description
    return ""

def test_easy_ocr(image_path):
    reader = easyocr.Reader(['th', 'en'])
    result = reader.readtext(image_path, detail=0)
    return " ".join(result)

def main(pdf_path):
    print(f"📄 Testing OCR (Google vs EasyOCR) on: {pdf_path}")
    
    # 1. Convert first page to image
    images = convert_from_path(pdf_path, last_page=1)
    if not images:
        print("❌ Failed to convert PDF to image")
        return
    
    img_path = "temp_test_easy.jpg"
    images[0].save(img_path, format='JPEG')
    
    with open(img_path, 'rb') as f:
        img_content = f.read()

    # 2. Run Google Vision
    print("🛰️ Running Google Vision API...")
    start_g = time.time()
    text_g = test_google_vision(img_content)
    end_g = time.time()
    
    # 3. Run EasyOCR
    print("🧠 Running Local EasyOCR (Thai + English)...")
    start_e = time.time()
    text_e = test_easy_ocr(img_path)
    end_e = time.time()
    
    # 4. Results Comparison
    print("\n" + "="*50)
    print("📊 COMPARISON RESULTS")
    print("="*50)
    print(f"⏱️ Google Vision Time: {end_g - start_g:.2f}s")
    print(f"⏱️ EasyOCR Time:       {end_e - start_e:.2f}s")
    print("-"*50)
    
    print("\n📝 [Google Vision Text (Snippet)]:")
    print(text_g[:500] + "...")
    
    print("\n📝 [EasyOCR Text (Snippet)]:")
    print(text_e[:500] + "...")
    
    # Save full results for inspection
    with open("ocr_comparison_easy.json", "w", encoding="utf-8") as f:
        json.dump({
            "google_vision": text_g,
            "easy_ocr": text_e
        }, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Full comparison saved to ocr_comparison_easy.json")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_easy.py <pdf_path>")
    else:
        main(sys.argv[1])
