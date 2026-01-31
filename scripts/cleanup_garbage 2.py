from google.cloud import discoveryengine_v1 as ds
from google.api_core.exceptions import NotFound, FailedPrecondition

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"
COLLECTION = "default_collection"

# OLD Engines to delete
ENGINES_TO_DELETE = [
    "deka-ultimate", 
    "law-ultimate"
]

# Unnecessary Stores to delete
STORES_TO_DELETE = [
    # Old Unstructured
    "deka-civil", "deka-criminal", "deka-labor", "deka-general",
    "law-civil", "law-criminal", "law-labor", "law-general",
    
    # Polluted Structured (Merged with noise)
    "deka-civil-struct", 
    "law-civil-struct"
    
    # Note: We KEEP 'deka-criminal-struct' and 'law-criminal-struct' as they are valid.
]

def cleanup():
    client_eng = ds.EngineServiceClient()
    client_ds = ds.DataStoreServiceClient()
    
    print("🧹 Starting Big Cleanup...")
    
    # 1. Delete Old Engines
    print("\n🧨 Deleting Unused Engines...")
    for eng_id in ENGINES_TO_DELETE:
        name = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/engines/{eng_id}"
        try:
            op = client_eng.delete_engine(name=name)
            print(f"   ⏳ Deleting {eng_id}...")
            # op.result() # Async is fine, don't wait too long
        except NotFound:
            print(f"   ❌ {eng_id} not found (Good)")
        except Exception as e:
            print(f"   ⚠️ Error {eng_id}: {e}")

    # 2. Delete Unused Stores
    print("\n🗑️ Deleting Unused Stores...")
    for store_id in STORES_TO_DELETE:
        name = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/dataStores/{store_id}"
        try:
            op = client_ds.delete_data_store(name=name)
            print(f"   ⏳ Deleting {store_id}...")
        except NotFound:
            print(f"   ❌ {store_id} not found (Good)")
        except FailedPrecondition as e:
            print(f"   ⚠️ Cannot delete {store_id} (Linked to Engine?): {e}")
        except Exception as e:
            print(f"   ⚠️ Error {store_id}: {e}")

if __name__ == "__main__":
    cleanup()
