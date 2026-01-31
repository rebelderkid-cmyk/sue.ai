from google.cloud import discoveryengine_v1 as ds
from google.api_core.exceptions import AlreadyExists

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"
COLLECTION = "default_collection"

# New Structured Stores Config (Fresh IDs to avoid soft-delete conflict)
STORES = {
    "deka-civil-clean-v2": "Civil Deka Clean V2",
    "deka-criminal-struct-v2": "Criminal Deka Struct V2",
    "deka-labor-struct-v2": "Labor Deka Struct V2",
    "deka-general-struct-v2": "General Deka Struct V2",
    
    "law-civil-clean-v2": "Civil Law Clean V2",
    "law-criminal-struct-v2": "Criminal Law Struct V2",
    "law-labor-struct-v2": "Labor Law Struct V2",
    "law-general-struct-v2": "General Law Struct V2"
}

ENGINES = {
    # Unified V3 Engine
    "sue-ai-legal-unified-v3": list(STORES.keys())
}

def create_stores():
    client = ds.DataStoreServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}"
    
    for store_id, display_name in STORES.items():
        print(f"🏗️ Creating Store: {store_id}...")
        ds_obj = ds.DataStore(
            display_name=display_name,
            industry_vertical=ds.IndustryVertical.GENERIC,
            solution_types=[ds.SolutionType.SOLUTION_TYPE_SEARCH],
            # content_config=ds.DataStore.ContentConfig.NO_CONTENT, # Let's omit this to use default (which supports structured upload via Import API) 
            # Actually, NO_CONTENT means we upload metadata only? No.
            # We want PUBLIC_WEBSITE or GOOGLE_DRIVE? No.
            # For Structured Data Import, usually we pick "Generic" and then import JSON. 
            # In Discovery Engine API v1beta, content_config can be STRUCTURED_DATA?
            # In v1, it's NO_CONTENT if we provide structured data via API/GCS without "parsed content" extraction.
            # Let's verify... Yes, NO_CONTENT is often used for Structured Data where we provide schema.
            # But wait, we want to search 'text'.
        )
        # Let's try creating with NO_CONTENT which implies we provide the schema/data ourselves.
        
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

def create_engines():
    client = ds.EngineServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}"
    
    for eng_id, stores in ENGINES.items():
        print(f"\n⚙️ Creating Engine: {eng_id}...")
        
        # Configure Engine
        config = ds.Engine.SearchEngineConfig(
            search_tier=ds.SearchTier.SEARCH_TIER_ENTERPRISE,
            search_add_ons=[ds.SearchAddOn.SEARCH_ADD_ON_LLM]
        )
        
        engine = ds.Engine(
            display_name=f"Ultimate {eng_id}",
            solution_type=ds.SolutionType.SOLUTION_TYPE_SEARCH,
            industry_vertical=ds.IndustryVertical.GENERIC,
            search_engine_config=config,
            data_store_ids=stores # Bind Stores here!
        )
        
        request = ds.CreateEngineRequest(
            parent=parent,
            engine_id=eng_id,
            engine=engine
        )
        
        try:
            op = client.create_engine(request=request)
            print(f"   Waiting for engine {eng_id}...")
            op.result()
            print("   ✅ Created!")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    create_stores()
    create_engines()
