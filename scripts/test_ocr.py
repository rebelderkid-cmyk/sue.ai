import os
import sys
import time
import json
import io
from pdf2image import convert_from_path
from google.cloud import vision
from paddleocr import PaddleOCR

def test_google_vision(image_content):
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_content)
    response = client.document_text_detection(image=image)
    if response.text_annotations:
        return response.text_annotations[0].description
    return ""

def test_paddle_ocr(image_path):
    # Use Thai language
    ocr = PaddleOCR(lang='th')
    result = ocr.ocr(image_path, cls=True)
    
    full_text = ""
    for idx in range(len(result)):
        res = result[idx]
        if res:
            for line in res:
                full_text += line[1][0] + " "
    return full_text

def main(pdf_path):
    print(f"📄 Testing OCR on: {pdf_path}")
    
    # 1. Convert first page to image
    images = convert_from_path(pdf_path, last_page=1)
    if not images:
        print("❌ Failed to convert PDF to image")
        return
    
    img_path = "temp_test_page.jpg"
    images[0].save(img_path, format='JPEG')
    
    with open(img_path, 'rb') as f:
        img_content = f.read()

    # 2. Run Google Vision
    print("🛰️ Running Google Vision API...")
    start_g = time.time()
    text_g = test_google_vision(img_content)
    end_g = time.time()
    
    # 3. Run PaddleOCR
    print("🚣 Running Local PaddleOCR...")
    start_p = time.time()
    text_p = test_paddle_ocr(img_path)
    end_p = time.time()
    
    # 4. Results Comparison
    print("\n" + "="*50)
    print("📊 COMPARISON RESULTS")
    print("="*50)
    print(f"⏱️ Google Vision Time: {end_g - start_g:.2f}s")
    print(f"⏱️ PaddleOCR Time:     {end_p - start_p:.2f}s")
    print("-"*50)
    
    print("\n📝 [Google Vision Text (Snippet)]:")
    print(text_g[:500] + "...")
    
    print("\n📝 [PaddleOCR Text (Snippet)]:")
    print(text_p[:500] + "...")
    
    # Save full results for inspection
    with open("ocr_comparison.json", "w", encoding="utf-8") as f:
        json.dump({
            "google_vision": text_g,
            "paddle_ocr": text_p
        }, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Full comparison saved to ocr_comparison.json")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_ocr.py <pdf_path>")
    else:
        main(sys.argv[1])
