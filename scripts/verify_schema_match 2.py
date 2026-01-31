import json
import sys

def get_keys_recursive(d, prefix=""):
    keys = set()
    if isinstance(d, dict):
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.add(full_key)
            # Recurse into structData and document_meta only (skip flexible fields like entities for strict check)
            if k in ["structData", "document_meta"]: 
                keys.update(get_keys_recursive(v, full_key))
    return keys

def verify():
    # Load Original
    print("📖 Reading Original: vertex_import_FINAL.jsonl")
    with open("vertex_import_FINAL.jsonl", "r") as f:
        orig = json.loads(f.readline())

    # Load V6 Sample
    print("📖 Reading V6 Sample: v6_sample.jsonl")
    with open("v6_sample.jsonl", "r") as f:
        v6 = json.loads(f.readline())

    print("\n🔍 --- COMPARISON REPORT ---")
    
    # Check Required Top Fields
    required_top = ["id", "structData", "content", "_id"]
    missing_top = [k for k in required_top if k not in v6]
    
    if missing_top:
        print(f"❌ CRITICAL: Missing Required Top-Level Fields: {missing_top}")
        if "_id" in missing_top:
             print("   (Note: '_id' is required for Vertex AI to avoid errors)")
    else:
        print("✅ Top-Level Fields: OK (id, _id, structData, content present)")

    # Compare StructData Deeply
    orig_struct = orig.get("structData", {})
    v6_struct = v6.get("structData", {})
    
    orig_keys = set(orig_struct.keys())
    v6_keys = set(v6_struct.keys())
    
    missing_in_v6 = orig_keys - v6_keys
    extra_in_v6 = v6_keys - orig_keys # This is fine (e.g. source_category), but let's list them
    
    if missing_in_v6:
        print(f"\n❌ ERROR: structData is MISSING fields from original: {missing_in_v6}")
        print("   ⚠️ This means the schema IS NOT PRESERVED.")
    else:
        print("\n✅ structData Preservation: PASSED")
        print("   (All original fields are present in v6)")

    if extra_in_v6:
        print(f"   ℹ️  Added fields (Enrichment): {extra_in_v6}")

    # Check Content Field (New Requirement)
    if "content" in v6:
        print(f"\n✅ Content Field: Present")
        print(f"   Data Sample: {str(v6['content'])[:100]}...")
    else:
        print("\n❌ ERROR: 'content' field is MISSING.")

    # Final Verdict
    if not missing_top and not missing_in_v6:
        print("\n🎉 VERDICT: SCHEMA MATCHES! Ready for Import.")
    else:
        print("\n⛔ VERDICT: SCHEMA MISMATCH. DO NOT IMPORT.")

if __name__ == "__main__":
    try:
        verify()
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
