from google.cloud import discoveryengine_v1 as ds

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"

def import_data():
    client = ds.DocumentServiceClient()
    
    # Mapping Flat JSONL folders (on GCS) to New Structured Stores
    mapping = [
        # Deka
        ("deka-civil-clean", "gs://main_legal_data/structured_flat_v2/deka-civil/*.jsonl"),
        ("deka-criminal-struct", "gs://main_legal_data/structured_flat_v2/deka-criminal/*.jsonl"),
        ("deka-labor-struct", "gs://main_legal_data/structured_flat_v2/deka-labor/*.jsonl"),
        ("deka-general-struct", "gs://main_legal_data/structured_flat_v2/deka-general/*.jsonl"),
        
        # Law
        ("law-civil-clean", "gs://main_legal_data/structured_flat_v2/law-civil/*.jsonl"),
        ("law-criminal-struct", "gs://main_legal_data/structured_flat_v2/law-criminal/*.jsonl"),
        ("law-labor-struct", "gs://main_legal_data/structured_flat_v2/law-labor/*.jsonl"),
        ("law-general-struct", "gs://main_legal_data/structured_flat_v2/law-general/*.jsonl"),
    ]
    
    print("🚀 Starting Structured Data Import...")
    
    for ds_id, uri in mapping:
        print(f"\n📥 Importing to {ds_id} form {uri}...")
        parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{ds_id}/branches/default_branch"
        
        try:
            request = ds.ImportDocumentsRequest(
                parent=parent,
                gcs_source=ds.GcsSource(input_uris=[uri], data_schema="custom"), # custom schema inferred from JSON? Or 'document'? 
                # For structured data, we just pass the GCS source.
                # However, we must ensure it's treated as JSONL. Default is auto-detect.
                reconciliation_mode=ds.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL
            )
            
            op = client.import_documents(request=request)
            print(f"   ⏳ Operation started: {op.operation.name}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    import_data()
