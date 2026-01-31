from google.cloud import discoveryengine_v1 as ds
from google.api_core.exceptions import NotFound

# SAFETY CHECK: DELETING MALFUNCTIONING NEW INFRASTRUCTURE
# PROTECTED: sue-ai-search_1768730959752 is EXCLUDED.
ENGINES = ["sue-ai-legal-unified-v2"]
STORES = [
    "deka-civil-clean", "deka-criminal-struct", "deka-labor-struct", "deka-general-struct",
    "law-civil-clean", "law-criminal-struct", "law-labor-struct", "law-general-struct"
]

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"
COLLECTION = "default_collection"

def delete_all():
    client_eng = ds.EngineServiceClient()
    client_ds = ds.DataStoreServiceClient()
    
    # 1. Delete Engines FIRST
    print("🧨 Deleting Engines...")
    for eng_id in ENGINES:
        name = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/engines/{eng_id}"
        try:
            op = client_eng.delete_engine(name=name)
            print(f"   Waiting for delete engine {eng_id}...")
            op.result()
            print(f"   ✅ Deleted {eng_id}")
        except NotFound:
            print(f"   ❌ Engine {eng_id} not found")
        except Exception as e:
            print(f"   ⚠️ Error deleting {eng_id}: {e}")
    
    # 2. Delete Stores
    print("\n🗑️ Deleting Data Stores...")
    for store_id in STORES:
        name = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/dataStores/{store_id}"
        try:
            op = client_ds.delete_data_store(name=name)
            print(f"   ⏳ Deleted {store_id} (Async)")
        except NotFound:
            print(f"   ❌ {store_id} not found")
        except Exception as e:
            print(f"   ⚠️ {e}")

if __name__ == "__main__":
    delete_all()
