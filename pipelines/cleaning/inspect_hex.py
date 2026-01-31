import pdfplumber

PDF_PATH = "downloads/2568/Deka_1-2537_(Ref58482).pdf"

with pdfplumber.open(PDF_PATH) as pdf:
    text = pdf.pages[0].extract_text()
    print("--- Extracted Text Sample ---")
    print(text[:200])
    print("\n--- Hex Dump of 'ขอกฎหมาย' context ---")
    # Finding the phrase "ข้อกฎหมาย" or whatever it looks like
    # The JSON showed: "ข", "", "อก", "ฎ"
    
    # Let's verify by printing chars and their hex
    for char in text[:100]:
        if ord(char) > 127: # Non-ASCII
            print(f"'{char}': U+{ord(char):04X}")
