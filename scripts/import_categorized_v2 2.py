from google.cloud import discoveryengine_v1 as discoveryengine

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"

def import_to_store(ds_id, gcs_uri):
    client = discoveryengine.DocumentServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{ds_id}/branches/default_branch"
    
    print(f"🚀 Importing from {gcs_uri} to {ds_id}...")
    
    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[gcs_uri],
            data_schema="custom"
        ),
        error_config=discoveryengine.ImportErrorConfig(
            gcs_prefix=f"gs://main_legal_data/errors/{ds_id}/"
        )
    )

    try:
        operation = client.import_documents(request=request)
        print(f"⏳ Op: {operation.operation.name}")
        return operation
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

if __name__ == "__main__":
    # Mapping to New High-Precision Stores
    # Mapping Categories (Folder Name) -> Data Store ID
    # Note: Using 'v6' which includes '_id' field and ID validation
    mapping = [
        # Deka (V2)
        ("deka-civil-clean-v2", "gs://main_legal_data/categorized_v7/deka_civil/*.jsonl"),
        ("deka-criminal-struct-v2", "gs://main_legal_data/categorized_v7/deka_criminal/*.jsonl"),
        ("deka-labor-struct-v2", "gs://main_legal_data/categorized_v7/deka_labor/*.jsonl"),
        ("deka-general-struct-v2", "gs://main_legal_data/categorized_v7/deka_general/*.jsonl"),
        
        # Law (V2)
        ("law-civil-clean-v2", "gs://main_legal_data/categorized_v7/law_civil/*.jsonl"),
        ("law-criminal-struct-v2", "gs://main_legal_data/categorized_v7/law_criminal/*.jsonl"),
        ("law-labor-struct-v2", "gs://main_legal_data/categorized_v7/law_labor/*.jsonl"),
        ("law-general-struct-v2", "gs://main_legal_data/categorized_v7/law_general/*.jsonl"),
    ]
    
    for ds_id, uri in mapping:
        import_to_store(ds_id, uri)
