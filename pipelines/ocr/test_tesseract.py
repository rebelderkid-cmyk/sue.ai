import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

# Configuration
PDF_PATH = "scrapers/ratchakitcha/downloads_poc/รัฐธรรมนูญแห่งราชอาณาจักรไทย พุทธศักราช ๒๔๗๕ แก้ไขเพิ่มเติม พุทธศักราช ๒๔๙๕.pdf"
TESS_DATA_DIR = os.path.abspath("pipelines/ocr/tessdata")

def run_tesseract_test():
    print(f"🚀 Processing PDF (Tesseract): {os.path.basename(PDF_PATH)}")
    
    # 1. Convert First Page to Image (Bytes mode to avoid path issues)
    print("📸 Converting PDF page 1 to image...")
    try:
        with open(PDF_PATH, "rb") as f:
            pdf_bytes = f.read()
        images = convert_from_path(PDF_PATH, first_page=1, last_page=1) # Path works if passed to docker/poppler, but let's see. 
        # Actually earlier we had issue with path in pdf2image, but convert_from_bytes was fine.
        # Let's use convert_from_bytes logic again just to be safe.
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
        
        img = images[0]
    except Exception as e:
        print(f"❌ PDF Error: {e}")
        return

    # 2. Configure Tesseract
    # Point to our local tessdata folder
    os.environ["TESSDATA_PREFIX"] = TESS_DATA_DIR
    
    print("✨ Running Tesseract OCR (Thai)...")
    try:
        text = pytesseract.image_to_string(img, lang='tha', config='--psm 3') # psm 3 = Auto page segmentation
        
        print("\n=== TESSERACT OUTPUT ===\n")
        print(text)
        print("\n========================\n")
        
        with open("pipelines/ocr/test_tesseract_output.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
    except Exception as e:
        print(f"❌ Tesseract Error: {e}")

if __name__ == "__main__":
    run_tesseract_test()
