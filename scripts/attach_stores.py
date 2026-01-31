from google.cloud import discoveryengine_v1 as ds
from google.protobuf import field_mask_pb2

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"

def attach_stores_to_engine(engine_id, new_store_ids):
    client = ds.EngineServiceClient()
    engine_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/engines/{engine_id}"
    
    # Get current engine state
    engine = client.get_engine(name=engine_path)
    current_stores = list(engine.data_store_ids)
    
    print(f"🛠 Engine: {engine.display_name} ({engine_id})")
    print(f"Current stores: {current_stores}")
    
    # Merge unique stores
    updated_stores = list(set(current_stores + new_store_ids))
    
    if len(updated_stores) == len(current_stores):
        print("✅ No new stores to add.")
        return

    # Update engine
    engine.data_store_ids = updated_stores
    update_mask = field_mask_pb2.FieldMask(paths=["data_store_ids"])
    
    print(f"Updating to: {updated_stores}...")
    operation = client.update_engine(engine=engine, update_mask=update_mask)
    print(f"✅ Update successful for {engine.display_name}")

if __name__ == "__main__":
    # 1. DEKA Engine
    attach_stores_to_engine("sue-ai-search_1768730959752", ["deka-civil", "deka-criminal"])
    
    # 2. LAW Engine
    attach_stores_to_engine("main-legal-search_1768906502953", ["law-civil", "law-criminal"])
