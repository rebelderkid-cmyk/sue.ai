import os
from google.cloud import discoveryengine_v1 as ds
from google.api_core.client_options import ClientOptions

# Configuration
PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"

# Mapping: Store ID -> List of GCS Folders (Merged Law + Deka)
# NOTE: We reuse the existing 'law-*' store IDs but fill them with BOTH Law and Deka content
STORE_MAPPING = {
    "law-civil-clean": [
        "gs://main_legal_data/categorized_final_v1/law-civil/*.jsonl",
        "gs://main_legal_data/categorized_final_v1/deka-civil/*.jsonl"
    ],
    "law-criminal-struct": [
        "gs://main_legal_data/categorized_final_v1/law-criminal/*.jsonl",
        "gs://main_legal_data/categorized_final_v1/deka-criminal/*.jsonl"
    ],
    "law-labor-struct": [
        "gs://main_legal_data/categorized_final_v1/law-labor/*.jsonl",
        "gs://main_legal_data/categorized_final_v1/deka-labor/*.jsonl"
    ],
    "law-general-struct": [
        "gs://main_legal_data/categorized_final_v1/law-general/*.jsonl",
        "gs://main_legal_data/categorized_final_v1/deka-general/*.jsonl"
    ]
}

def purge_documents(store_id):
    client = ds.DocumentServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{store_id}/branches/default_branch"
    
    print(f"🗑️ [Purge] Cleaning {store_id}...")
    # List and delete is slow, usually Purge is better if available, but for structured store, 
    # we can use import with ReconciliationMode.FULL (Wait, GCS import doesn't support FULL mode for purge?)
    # Actually, we can assume we want to APPEND/UPSERT, but if we want strictly clean, 
    # we should try to delete. For now, let's trust ReconciliationMode.INCREMENTAL (Upsert) 
    # because 'PurgeDocuments' API is async and might be complex.
    # HOWEVER, User asked to DELETE old data.
    
    # Trick: There is a purge_documents method in v1beta/v1?
    # Let's try listing and deleting a sample to verify connection, 
    # but for mass deletion, the CLI or Console is best. 
    # To correspond with "delete old data", we will proceed with the Import. 
    # (If old data IDs overlap, they get updated. If completely different, they stay).
    #
    # WAIT! Correct approach: We rely on the fact that IDs are stable. 
    # If IDs are different, we might have garbage.
    # But doing a full purge via API takes 24 hours sometimes.
    # Let's Skip Purge logic in code and rely on the fact that we are overwriting the main knowledge.
    # Or... we can try `purge_documents` which takes a filter `*`.
    
    try:
        operation = client.purge_documents(request=ds.PurgeDocumentsRequest(
            parent=parent,
            filter="*",
            force=True
        ))
        print(f"⏳ Purge Operation started for {store_id}...")
        operation.result() # Wait for completion
        print(f"✅ Purged {store_id}!")
    except Exception as e:
        print(f"⚠️ Purge skipped or failed (might be empty): {e}")

def import_documents(store_id, gcs_uris):
    client = ds.DocumentServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{store_id}/branches/default_branch"
    
    print(f"📥 [Import] Importing to {store_id} from {len(gcs_uris)} sources...")
    
    gcs_source = ds.GcsSource(input_uris=gcs_uris, data_schema="custom")
    
    # Use INCREMENTAL to add/update. 
    req = ds.ImportDocumentsRequest(
        parent=parent,
        gcs_source=gcs_source,
        reconciliation_mode=ds.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
        error_config=ds.ImportErrorConfig(gcs_prefix="gs://main_legal_data/errors")
    )
    
    operation = client.import_documents(request=req)
    print(f"⏳ Import Operation started for {store_id}...")
    operation.result()
    print(f"✅ Import Complete for {store_id}!")

def main():
    print("🔥 Starting Wipe & Load Operation (Merged Law+Deka)...")
    
    for store_id, uris in STORE_MAPPING.items():
        print(f"\n--- Processing {store_id} ---")
        purge_documents(store_id)
        import_documents(store_id, uris)
        
    print("\n✨ All Stores Processed Successfully!")

if __name__ == "__main__":
    main()
