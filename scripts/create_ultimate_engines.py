from google.cloud import discoveryengine_v1 as ds

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"

def create_multi_store_engine(engine_id, display_name, data_store_ids):
    client = ds.EngineServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection"
    
    engine = ds.Engine(
        display_name=display_name,
        solution_type=ds.SolutionType.SOLUTION_TYPE_SEARCH,
        industry_vertical=ds.IndustryVertical.GENERIC,
        data_store_ids=data_store_ids,
        search_engine_config=ds.Engine.SearchEngineConfig(
            search_tier=ds.SearchTier.SEARCH_TIER_ENTERPRISE,
            search_add_ons=[ds.SearchAddOn.SEARCH_ADD_ON_LLM]
        )
    )
    
    print(f"🚀 Creating Multi-Store Engine: {display_name}...")
    try:
        operation = client.create_engine(
            parent=parent,
            engine=engine,
            engine_id=engine_id
        )
        print(f"⏳ Operation: {operation.operation.name}")
        return operation.result()
    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    # Create ONE Unified Engine for everything
    all_stores = [
        "deka-civil-clean", "deka-criminal-struct", "deka-labor-struct", "deka-general-struct",
        "law-civil-clean", "law-criminal-struct", "law-labor-struct", "law-general-struct"
    ]
    
    create_multi_store_engine(
        "sue-ai-legal-unified-v2", 
        "Sue AI Legal Unified V2", 
        all_stores
    )
