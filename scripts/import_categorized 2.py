import os
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
            gcs_prefix="gs://main_legal_data/errors/"
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
    # เราจะ Import หมวดหมู่ต่างๆ เข้าสู่ Store ที่เหมาะสม
    # สำหรับ Deka เราจะใช้ deka_1768730204117
    # สำหรับ Law เราจะใช้ main-legal_1768906525188
    
    mapping = [
        ("deka_1768730204117", "gs://main_legal_data/categorized/deka_civil/*.jsonl"),
        ("deka_1768730204117", "gs://main_legal_data/categorized/deka_criminal/*.jsonl"),
        ("deka_1768730204117", "gs://main_legal_data/categorized/deka_labor/*.jsonl"),
        ("deka_1768730204117", "gs://main_legal_data/categorized/deka_general/*.jsonl"),
        ("main-legal_1768906525188", "gs://main_legal_data/categorized/law_civil/*.jsonl"),
        ("main-legal_1768906525188", "gs://main_legal_data/categorized/law_criminal/*.jsonl"),
        ("main-legal_1768906525188", "gs://main_legal_data/categorized/law_labor/*.jsonl"),
        ("main-legal_1768906525188", "gs://main_legal_data/categorized/procedure/*.jsonl"),
    ]
    
    for ds_id, uri in mapping:
        import_to_store(ds_id, uri)
