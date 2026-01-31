from google.cloud import discoveryengine_v1 as ds

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"

# New Categorized Stores
STORES = ["deka-civil", "deka-criminal", "law-civil", "law-criminal"]

def verify():
    client = ds.DocumentServiceClient()
    
    print(f"🕵️ Verifying Documents in {len(STORES)} Stores...")
    print("-" * 50)

    for ds_id in STORES:
        parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{ds_id}/branches/default_branch"
        print(f"\n📂 Store: {ds_id}")
        
        try:
            # List 1 doc just to verify existence
            request = ds.ListDocumentsRequest(parent=parent, page_size=1)
            page = client.list_documents(request=request)
            
            found = False
            for doc in page:
                found = True
                print(f"   ✅ SUCCESS! Found Doc ID: {doc.id}")
                # print(f"      Title: {doc.struct_data.get('title', 'N/A')}") # Might not be available yet
                break
            
            if not found:
                print("   ⚠️  Empty (Processing or Failed)")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    verify()
