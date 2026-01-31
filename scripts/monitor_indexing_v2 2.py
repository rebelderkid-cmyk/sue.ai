from google.cloud import discoveryengine_v1 as ds
import time
import sys

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"
COLLECTION = "default_collection"

# All 8 Clean/Structured Stores
STORES = [
    "deka-civil-clean", "deka-criminal-struct", "deka-labor-struct", "deka-general-struct",
    "law-civil-clean", "law-criminal-struct", "law-labor-struct", "law-general-struct"
]

def monitor():
    client = ds.DocumentServiceClient()
    
    print(f"🕵️  Monitor Indexing Status (Target: {len(STORES)} Stores)")
    print("-" * 60)

    while True:
        status_line = []
        all_ready_count = 0
        
        for store_id in STORES:
            parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/dataStores/{store_id}/branches/default_branch"
            try:
                request = ds.ListDocumentsRequest(parent=parent, page_size=1)
                page = client.list_documents(request=request)
                
                count = 0
                for _ in page: count += 1
                
                if count > 0:
                    status_line.append(f"✅ {store_id.replace('struct','').replace('clean','').strip('-')}:OK")
                    all_ready_count += 1
                else:
                    status_line.append(f"⏳ {store_id.replace('struct','').replace('clean','').strip('-')}:Wait")
                    
            except Exception as e:
                status_line.append(f"❌ {store_id}:Err")
        
        # Print
        print("\r" + " | ".join(status_line), end="")
        sys.stdout.flush()
        
        if all_ready_count == len(STORES):
            print("\n🚀 All 8 Stores are READY!")
            break
            
        time.sleep(10)

if __name__ == "__main__":
    monitor()
