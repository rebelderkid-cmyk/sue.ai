import sys
import os
import time

# Append paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PHASE2 = os.path.join(SCRIPT_DIR, "Phase2_OCR")
sys.path.append(PHASE2)

from pythainlp import word_tokenize, correct, spell
from pythainlp.util import normalize, Trie
from pythainlp.soundex import lk82, udom83

def demo_ocr_and_clean():
    print("🚀 PyThaiNLP Capabilities Demo 🚀")
    print("-" * 50)

    # 1. Problem: Serious OCR Corruptions
    corrupt_pairs = [
        ("ร่างกิจการบุคคล", "ราชกิจจานุเบกษา"),
        ("สภานั้น", "สถาบัน"),
        ("มีคุณยน", "มิถุนายน"),
        ("สัมผัส", "ล้มละลาย") 
    ]
    
    # 2. Capability: Normalize
    print("\n[Capability 1: Normalization]")
    unnormalized = "เ ก า ะ"
    norm = normalize(unnormalized)
    print(f"'{unnormalized}' -> '{norm}' (Removes excess spacing/PUA)")

    # 3. Capability: Soundex (Phonetic Comparison)
    print("\n[Capability 2: Soundex (Phonetic Similarity)]")
    print("Checking if corruptions sound similar to targets...")
    
    for corrupt, target in corrupt_pairs:
        # Using LK82 and Udom83 systems
        s1_lk82 = lk82(corrupt)
        s2_lk82 = lk82(target)
        
        match = (s1_lk82 == s2_lk82)
        print(f"'{corrupt}' vs '{target}'")
        print(f"   LK82: {s1_lk82} vs {s2_lk82} ({'MATCH' if match else 'Diff'})")
        
        # If Soundex matches, it confirms 'Mishearing' or similar shape errors often result in similar sounds
        
    # 4. Capability: Custom Dictionary / Trie
    print("\n[Capability 3: Custom Dictionary for Correction]")
    
    # Standard tokenization splits 'ร่างกิจการบุคคล' -> ['ร่าง', 'กิจการ', 'บุคคล'] (All valid words!)
    # This explains why strict spell checker fails.
    
    tokens_std = word_tokenize("ร่างกิจการบุคคล")
    print(f"Standard Tokenization: {tokens_std} (All valid words, so Spell Check skips)")
    
    # Solution: Add the CORRECT phrase to a custom Trie to force recognition
    print("Creating Custom Trie with 'ราชกิจจานุเบกษา'...")
    custom_words = {"ราชกิจจานุเบกษา", "สถาบันการเงิน", "ล้มละลาย", "มิถุนายน"}
    # We can also add common corruptions to map them if we wrote a custom tokenizer, 
    # but usually we use a dictionary-based replacement.
    
    # Simple Dictionary Replacement (The most robust for specific OCR errors)
    fix_dict = {
        "ร่างกิจการบุคคล": "ราชกิจจานุเบกษา",
        "สภานั้น": "สถาบัน",
        "มีคุณยน": "มิถุนายน",
        "สัมผัส": "ล้มละลาย" 
    }
    
    def apply_fix(text):
        for wrong, right in fix_dict.items():
            text = text.replace(wrong, right)
        return text

    for corrupt, _ in corrupt_pairs:
        fixed = apply_fix(corrupt)
        print(f"Fixed: '{corrupt}' -> '{fixed}'")

    print("\n[Summary]")
    print("PyThaiNLP is powerful for:")
    print("1. Detection via Soundex (if errors are phonetically similar)")
    print("2. Normalization (removing invisible junk)")
    print("3. Custom Tokenization (if we add domain terms to Trie)")
    print("For 'Wrong Valid Words' (Contextual Errors), explicit dictionary replacement is best.")

if __name__ == "__main__":
    demo_ocr_and_clean()
