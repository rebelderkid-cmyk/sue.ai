import pypdf
import sys

def debug_pdf(file_path):
    try:
        reader = pypdf.PdfReader(file_path)
        print(f"--- Debugging: {file_path} ---")
        print(f"Total Pages: {len(reader.pages)}")
        
        full_text = ""
        for i, page in enumerate(reader.pages[:3]):
            text = page.extract_text()
            print(f"\n[Page {i+1} Raw Text]:")
            print(repr(text))
            full_text += text
            
        print(f"\nTotal Text Length: {len(full_text)}")
        print(f"Cleaned Text Length: {len(full_text.strip())}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug_pdf(sys.argv[1])
