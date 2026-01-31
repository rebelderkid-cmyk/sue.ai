import os
from google.cloud import discoveryengine_v1 as discoveryengine
from google.protobuf.json_format import MessageToDict

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"

def list_data_stores():
    client = discoveryengine.DataStoreServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection"
    
    print(f"🔍 Listing Data Stores in {parent}...")
    try:
        response = client.list_data_stores(parent=parent)
        stores = []
        for ds in response:
            print(f"✅ Found Data Store: {ds.display_name} ({ds.name})")
            stores.append(ds)
        return stores
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def import_documents(data_store_id, gcs_uri):
    client = discoveryengine.DocumentServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{data_store_id}/branches/default_branch"
    
    print(f"🚀 Importing documents from {gcs_uri} to {data_store_id}...")
    
    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[gcs_uri],
            data_schema="custom" # or 'content' depending on schema. Using 'custom' for structured JSONL.
        ),
        # reimport_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.FULL # Use with caution
        error_config=discoveryengine.ImportErrorConfig(
            gcs_prefix="gs://sue-ai-pdfs-storage/errors/"
        )
    )

    try:
        operation = client.import_documents(request=request)
        print("⏳ Import started... (Operation ID returned)")
        print(f"Operation Name: {operation.operation.name}")
        
        # result = operation.result() # Wait for completion (might take long)
        # print(f"✅ Import Completed: {result}")
        print("⚠️ Returning immediately. Check Cloud Console for progress.")
    except Exception as e:
        print(f"❌ Import Failed: {e}")

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "list"
    
    if mode == "list":
        stores = list_data_stores()
        if not stores:
            print("No data stores found or error occurred.")
    elif mode == "import":
        ds_id = sys.argv[2] if len(sys.argv) > 2 else None
        gcs_uri = sys.argv[3] if len(sys.argv) > 3 else "gs://sue-ai-pdfs-storage/metadata/full_dataset_v1.jsonl"
        
        if not ds_id:
            print("Usage: python manage_vertex.py import <DATA_STORE_ID> <GCS_URI>")
        else:
            import_documents(ds_id, gcs_uri)
