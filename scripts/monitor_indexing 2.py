from google.cloud import discoveryengine_v1 as ds
import time
import sys

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"
COLLECTION = "default_collection"

# New Structured Stores
STORES = ["deka-civil-clean", "law-civil-clean", "deka-criminal-struct", "law-criminal-struct"]

def monitor():
    client = ds.DocumentServiceClient()
    
    print(f"🕵️  Monitor Indexing Status (Target: {len(STORES)} Structured Stores)")
    print("-" * 60)

    while True:
        status_line = []
        all_done = True
        
        for store_id in STORES:
            parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/dataStores/{store_id}/branches/default_branch"
            try:
                # Just list 1 doc to see if anything is there
                request = ds.ListDocumentsRequest(parent=parent, page_size=1)
                page = client.list_documents(request=request)
                
                count = 0
                for _ in page: count += 1
                
                if count > 0:
                    status_line.append(f"✅ {store_id}: READY")
                else:
                    status_line.append(f"⏳ {store_id}: Waiting...")
                    all_done = False
                    
            except Exception as e:
                status_line.append(f"❌ {store_id}: Error ({str(e)[:20]}...)")
                all_done = False
        
        # Clear line and print
        print("\r" + " | ".join(status_line), end="")
        sys.stdout.flush()
        
        if all_done:
            print("\n🚀 All Stores Indexed Successfully!")
            break
            
        time.sleep(5)

if __name__ == "__main__":
    monitor()
