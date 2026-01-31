from google.cloud import vision
from pdf2image import convert_from_path
import io
import sys
import os

def test_ocr(file_path):
    print(f"🔬 Testing Vision API on: {file_path}")
    try:
        # 1. Convert PDF to Image
        print("   Converting PDF to Image...")
        images = convert_from_path(file_path, first_page=1, last_page=1)
        if not images:
            print("❌ Failed to convert PDF to image.")
            return

        # 2. Prep Image for Vision API
        img_byte_arr = io.BytesIO()
        images[0].save(img_byte_arr, format='JPEG')
        content = img_byte_arr.getvalue()
        
        # 3. Call Vision API
        print("   Calling Google Vision API...")
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        
        if response.error.message:
            print(f"❌ API Error: {response.error.message}")
            return

        if response.text_annotations:
            print("✅ OCR Success! First 200 chars:")
            print("-" * 50)
            print(response.text_annotations[0].description[:200])
            print("-" * 50)
        else:
            print("⚠️ No text found in image.")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_ocr(sys.argv[1])
    else:
        print("Usage: python3 test_vision_direct.py <pdf_path>")
