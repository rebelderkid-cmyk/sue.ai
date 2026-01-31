from google.cloud import discoveryengine_v1 as ds
import time

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"

def force_import():
    client = ds.DocumentServiceClient()
    ds_id = "deka-civil"
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{ds_id}/branches/default_branch"
    
    gcs_uri = "gs://main_legal_data/categorized/deka_civil/*.jsonl"
    
    print(f"🔥 Force Importing {gcs_uri} to {ds_id}...")
    
    request = ds.ImportDocumentsRequest(
        parent=parent,
        gcs_source=ds.GcsSource(input_uris=[gcs_uri], data_schema="custom"),
    )
    
    try:
        operation = client.import_documents(request=request)
        print(f"⏳ Started Op: {operation.operation.name}")
        
        # Wait for a bit and check metadata
        time.sleep(10)
        op_res = client.get_operation(name=operation.operation.name)
        print(f"📊 Op Status at 10s: {op_res.done}")
        if op_res.error.message:
            print(f"❌ Error Detail: {op_res.error.message}")
            
    except Exception as e:
        print(f"❌ Initial Failure: {e}")

if __name__ == "__main__":
    force_import()
