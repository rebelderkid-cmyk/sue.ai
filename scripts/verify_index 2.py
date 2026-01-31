from google.cloud import discoveryengine_v1 as ds

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"

def count_docs(ds_id):
    client = ds.DocumentServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{ds_id}/branches/default_branch"
    
    try:
        # Use list_documents with a small page size to see if anything exists
        docs = client.list_documents(parent=parent, page_size=1)
        count = 0
        for _ in docs:
            count += 1
            break # Just need to know if at least 1 exists
        
        print(f"📦 Data Store: {ds_id} | Indexing Status: {'Active (Docs Found)' if count > 0 else 'EMPTY or INDEXING...'}")
    except Exception as e:
        print(f"❌ Error Checking {ds_id}: {e}")

if __name__ == "__main__":
    stores = ["deka-civil", "deka-criminal", "law-civil", "law-criminal", "deka_1768730204117", "main-legal_1768906525188"]
    for s in stores:
        count_docs(s)
