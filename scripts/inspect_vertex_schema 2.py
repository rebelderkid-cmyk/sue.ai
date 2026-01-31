import os
import json
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions
from dotenv import load_dotenv

# Load env variables
load_dotenv("src/backend-go/.env") # Try to load from Go backend env

PROJECT_ID = "gen-lang-client-0464468580"
DATA_STORE_ID = "deka-civil-clean" # Target the new store
LOCATION = "global"

def inspect_one_doc():
    print(f"🔎 Inspecting Vertex AI Store: {DATA_STORE_ID} (Project: {PROJECT_ID})")
    
    # Use DocumentService to see RAW stored format, not search results
    client = discoveryengine.DocumentServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}/branches/default_branch"
    
    request = discoveryengine.ListDocumentsRequest(
        parent=parent, 
        page_size=1
    )
    
    results = client.list_documents(request=request)
    
    for doc in results:
        print(f"\n📄 Found Document ID: {doc.id}")
        
        print("\n--- [1] StructData Fields ---")
        if hasattr(doc, "struct_data"):
            data = dict(doc.struct_data)
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("(None)")
            
        print("\n--- [2] DerivedStructData Fields ---")
        if hasattr(doc, "derived_struct_data"):
            data = dict(doc.derived_struct_data)
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("(None)")

        print("\n--- [3] JsonData (String) ---")
        if hasattr(doc, "json_data") and doc.json_data:
             print(doc.json_data)
        else:
             print("(None)")
             
        break # Inspect only one

if __name__ == "__main__":
    inspect_one_doc()
