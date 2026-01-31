import google.generativeai as genai
import os
import time

# --- CONFIG ---
API_KEY = "AIzaSyB6t5VFdMSX-rMMVQ7rmvpe_dxqNHIIamA"
MODEL_NAME = "gemini-2.0-flash" # Upgraded to 2.0 Flash!
TEST_FILE_PATH = "/home/rinne/test_doc.pdf"

def test_gemini_ocr():
    print(f"🔑 Configuring Gemini API...")
    genai.configure(api_key=API_KEY)
    
    # Check if file exists
    if not os.path.exists(TEST_FILE_PATH):
        print(f"❌ Error: File not found at {TEST_FILE_PATH}")
        return

    print(f"📄 Uploading {TEST_FILE_PATH} to Gemini File API...")
    try:
        sample_file = genai.upload_file(path=TEST_FILE_PATH, display_name="Legal Doc Test")
        print(f"   Upload successful. URI: {sample_file.uri}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return

    # Verify file is ready
    print("⏳ Waiting for processing...", end="", flush=True)
    while sample_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(2)
        sample_file = genai.get_file(sample_file.name)
    
    if sample_file.state.name == "FAILED":
        print("\n❌ File processing failed.")
        return
    
    print(f" DONE! State: {sample_file.state.name}")

    print(f"\n🧠 Generating content using {MODEL_NAME}...")
    try:
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        
        prompt = """
        You are an expert Thai legal assistant. 
        Perform OCR on this document and extract the following information in JSON format:
        1. "title": Document title
        2. "text_content": The full text content readable in Thai.
        3. "summary": A brief summary of the document.
        
        If the document is a dummy test file, just say "Test Document Detected" and summarize it.
        """
        
        response = model.generate_content([sample_file, prompt])
        
        print("\n✅ API Response Received:")
        print("-" * 40)
        print(response.text)
        print("-" * 40)
        
        # Cleanup
        try:
            genai.delete_file(sample_file.name)
            print("🧹 Cleanup: File deleted from cloud.")
        except: pass
        
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")

if __name__ == "__main__":
    test_gemini_ocr()
