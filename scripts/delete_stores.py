from google.cloud import discoveryengine_v1 as ds
from google.api_core.exceptions import NotFound

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"
COLLECTION = "default_collection"

# List of Stores to DELETE
STORES = ["deka-civil", "deka-criminal", "deka-labor", "deka-general", "law-civil", "law-criminal", "law-labor", "law-general", "law-ultimate", "deka-ultimate"] 
# Note: I'm deleting the engines (ultimate) too if they bound to these stores, but let's delete stores first.
# Actually, delete stores is enough, engines might need to be re-created or updated.

def delete_stores():
    client = ds.DataStoreServiceClient()
    
    for store_id in STORES:
        name = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/dataStores/{store_id}"
        print(f"🗑️ Deleting {store_id}...")
        try:
            # Check if exists first? No, just delete
            operation = client.delete_data_store(name=name)
            print(f"   ⏳ Delete Operation started: {operation.operation.name}")
            # We won't wait for all, just launch them
        except NotFound:
            print(f"   ❌ Not Found (Already deleted?)")
        except Exception as e:
            print(f"   ⚠️ Error: {e}")

if __name__ == "__main__":
    delete_stores()
