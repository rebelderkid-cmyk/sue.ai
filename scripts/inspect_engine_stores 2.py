from google.cloud import discoveryengine_v1 as ds

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"
COLLECTION = "default_collection"
ENGINE_ID = "sue-ai-search_1768730959752"

def check_engine():
    client = ds.EngineServiceClient()
    name = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/engines/{ENGINE_ID}"
    
    try:
        engine = client.get_engine(name=name)
        print(f"🛡️  Engine: {engine.display_name} ({engine.name})")
        print(f"📦 Attached Data Stores: {engine.data_store_ids}")
        return engine.data_store_ids
    except Exception as e:
        print(f"❌ Error getting engine: {e}")
        return []

if __name__ == "__main__":
    check_engine()
