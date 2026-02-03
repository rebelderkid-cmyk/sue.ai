import os
import google.generativeai as genai
from pdf2image import convert_from_path
import PIL.Image

# Configuration
PDF_PATH = "scrapers/ratchakitcha/downloads_poc/รฐธรรมนญแหงราชอาณาจกรไทย พทธศกราช ๒๔๗๕ แกไขเพมเตม พทธศกราช ๒๔๙๕.pdf"
API_KEY = os.environ.get("GEMINI_API_KEY")

def run_vision_test():
    if not API_KEY:
        print("❌ Error: GEMINI_API_KEY environment variable is not set.")
        return

    print(f"🚀 Processing: {PDF_PATH}")
    
    # 1. Convert PDF to Image (First page only)
    print("📸 Converting PDF to Image...")
    try:
        images = convert_from_path(PDF_PATH, first_page=1, last_page=1)
        if not images:
            print("❌ Failed to convert PDF to image.")
            return
        
        img = images[0]
        # Resize if too large (Gemini limit)
        if img.width > 3000 or img.height > 3000:
            img.thumbnail((3000, 3000))
            
        print(f"✅ Image ready: {img.size}")
    except Exception as e:
        print(f"❌ PDF Error: {e}")
        return

    # 2. Setup Gemini
    print("✨ Sending to Gemini 2.0 Flash...")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = """
    Role: Professional Thai Legal Archivist.
    Task: Transcribe the text from this image EXACTLY as it appears.
    
    Guidelines:
    1. Output ONLY the Thai text.
    2. Preserve old spellings if present (do not modernize).
    3. Format headers/titles correctly using Markdown (#, ##).
    4. Ignore page numbers or noise.
    """

    try:
        response = model.generate_content([prompt, img])
        print("\n=== GEMINI OUTPUT ===\n")
        print(response.text)
        print("\n=====================\n")
        
        # Save output
        with open("pipelines/ocr/test_vision_output.md", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("💾 Saved to pipelines/ocr/test_vision_output.md")
        
    except Exception as e:
        print(f"❌ Gemini Error: {e}")

if __name__ == "__main__":
    run_vision_test()
