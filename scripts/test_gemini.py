import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models
import os
import json
import time

# --- CONFIG ---
PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "us-central1"

# List of models to try
MODEL_NAMES = [
    "gemini-1.5-flash-001",
    "gemini-1.5-pro-preview-0409",
    "gemini-1.5-flash-preview-0514",
    "gemini-1.0-pro-001",
    "gemini-pro"
]

TEST_FILE_PATH = "/home/rinne/test_doc.pdf" # Absolute path

def init_vertex():
    vertexai.init(project=PROJECT_ID, location=LOCATION)

def test_vision_extraction(file_path):
    # Read file as bytes ONCE
    try:
        with open(file_path, "rb") as f:
            data = f.read()
    except Exception as e:
        print(f"❌ Critical: Cannot open PDF file: {e}")
        return

    document_part = Part.from_data(data, mime_type="application/pdf")
    
    prompt = """
    Extract Knowledge Graph from this legal document.
    Output JSON.
    """
    
    generation_config = {"max_output_tokens": 8192, "temperature": 0.1}

    print(f"🚀 Starting Multi-Model Test with file: {file_path} ({len(data)} bytes)...")
    
    success = False
    for model_name in MODEL_NAMES:
        print(f"👉 Trying model: [{model_name}] ...")
        try:
            model = GenerativeModel(model_name)
            responses = model.generate_content(
                [document_part, prompt],
                generation_config=generation_config,
                stream=False,
            )
            
            print(f"✅ SUCCESS with [{model_name}]!")
            print("-" * 20)
            print(responses.text[:500] + "...")
            print("-" * 20)
            success = True
            break # Stop after first success
            
        except Exception as e:
            print(f"   ❌ Failed with {model_name}: {e}")
            time.sleep(1) # Brief pause

    if not success:
        print("💀 All models failed. Please check API handling or Quota.")

if __name__ == "__main__":
    init_vertex()
    
    # Find a sample PDF to test
    # We will look for a small PDF in the index folder or zip
    target_pdf = None
    
    # Logic to find a random PDF from existing data
    search_dirs = ["/home/rinne/temp_index", "/mnt/data/downloads/zip"]
    for root, dirs, files in os.walk("/mnt/data/downloads/zip"):
         for file in files:
             if file.endswith(".pdf"):
                 target_pdf = os.path.join(root, file)
                 break
         if target_pdf: break
    
    if target_pdf:
        test_vision_extraction(target_pdf)
    else:
        print("⚠️ No PDF found easily. Please unzip one manually or specify path.")
