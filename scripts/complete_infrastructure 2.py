from google.cloud import discoveryengine_v1 as ds
from google.api_core.exceptions import AlreadyExists

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"
COLLECTION = "default_collection"

# 1. Missing Stores to Create
NEW_STORES = {
    "deka-labor-struct": "Labor Deka Cases (Structured)",
    "deka-general-struct": "General/Bankruptcy Deka Cases (Structured)",
    "law-labor-struct": "Labor Laws (Structured)",
    "law-general-struct": "General Laws/Gazette (Structured)"
}

# 2. Final Engine Mapping (All included)
ENGINE_UPDATES = {
    "deka-ultimate-struct": ["deka-civil-clean", "deka-criminal-struct", "deka-labor-struct", "deka-general-struct"],
    "law-ultimate-struct": ["law-civil-clean", "law-criminal-struct", "law-labor-struct", "law-general-struct"]
}

def create_missing_stores():
    client = ds.DataStoreServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}"
    
    for store_id, display_name in NEW_STORES.items():
        print(f"🏗️ Creating Store: {store_id}...")
        ds_obj = ds.DataStore(
            display_name=display_name,
            industry_vertical=ds.IndustryVertical.GENERIC,
            solution_types=[ds.SolutionType.SOLUTION_TYPE_SEARCH],
        )
        
        request = ds.CreateDataStoreRequest(
            parent=parent,
            data_store_id=store_id,
            data_store=ds_obj
        )
        
        try:
            op = client.create_data_store(request=request)
            print(f"   Waiting for creation {store_id}...")
            op.result()
            print("   ✅ Created!")
        except AlreadyExists:
            print("   ⚠️ Already Exists")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def update_engines():
    client = ds.EngineServiceClient()
    
    for eng_id, stores in ENGINE_UPDATES.items():
        print(f"\n⚙️ Updating Engine: {eng_id} to include All Categories...")
        
        name = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/engines/{eng_id}"
        
        engine = ds.Engine(
            name=name,
            data_store_ids=stores
        )
        
        from google.protobuf.field_mask_pb2 import FieldMask
        update_mask = FieldMask(paths=["data_store_ids"])
        
        request = ds.UpdateEngineRequest(
            engine=engine,
            update_mask=update_mask
        )
        
        try:
            op = client.update_engine(request=request)
            print(f"   Waiting for update {eng_id}...")
            res = op.result()
            print(f"   ✅ Updated! Stores: {res.data_store_ids}")
        except Exception as e:
            print(f"   ❌ Error updating engine: {e}")

if __name__ == "__main__":
    create_missing_stores()
    update_engines()
