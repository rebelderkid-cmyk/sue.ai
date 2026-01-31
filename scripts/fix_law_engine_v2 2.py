from google.cloud import discoveryengine_v1 as ds
from google.api_core.exceptions import NotFound

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"
COLLECTION = "default_collection"

ENG_ID = "law-ultimate-struct"
# All 4 Law Stores
STORES = ["law-civil-clean", "law-criminal-struct", "law-labor-struct", "law-general-struct"]

def recreate_law_engine():
    client = ds.EngineServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}"
    name = f"{parent}/engines/{ENG_ID}"
    
    # 1. Delete
    print(f"🧨 Deleting Engine {ENG_ID}...")
    try:
        op = client.delete_engine(name=name)
        print("   Waiting for deletion...")
        op.result()
        print("   ✅ Deleted!")
    except NotFound:
        print("   ❌ Not found (Already deleted?)")
    except Exception as e:
        print(f"   ⚠️ Error deleting: {e}")

    # 2. Create
    print(f"⚙️ Re-Creating Engine {ENG_ID} with stores: {STORES}...")
    config = ds.Engine.SearchEngineConfig(
        search_tier=ds.SearchTier.SEARCH_TIER_ENTERPRISE,
        search_add_ons=[ds.SearchAddOn.SEARCH_ADD_ON_LLM]
    )
    
    engine = ds.Engine(
        display_name="Ultimate Law Search (Re-created)",
        solution_type=ds.SolutionType.SOLUTION_TYPE_SEARCH,
        industry_vertical=ds.IndustryVertical.GENERIC,
        search_engine_config=config,
        data_store_ids=STORES
    )
    
    req = ds.CreateEngineRequest(
        parent=parent,
        engine_id=ENG_ID,
        engine=engine
    )
    
    try:
        op = client.create_engine(request=req)
        print("   Waiting for creation...")
        op.result()
        print("   ✅ Created Successfully!")
    except Exception as e:
        print(f"   ❌ Error creating: {e}")

if __name__ == "__main__":
    recreate_law_engine()
