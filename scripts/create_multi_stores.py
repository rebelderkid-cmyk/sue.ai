from google.cloud import discoveryengine_v1 as discoveryengine

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"

def create_data_store(ds_id, display_name):
    client = discoveryengine.DataStoreServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection"
    
    ds = discoveryengine.DataStore(
        display_name=display_name,
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
    )
    
    print(f"🛠 Creating Data Store: {display_name} ({ds_id})...")
    try:
        operation = client.create_data_store(
            parent=parent,
            data_store=ds,
            data_store_id=ds_id
        )
        print(f"⏳ Op: {operation.operation.name}")
        return operation.result()
    except Exception as e:
        print(f"⚠️ Error or already exists: {e}")

if __name__ == "__main__":
    stores = [
        ("deka-civil", "Deka Civil"),
        ("deka-criminal", "Deka Criminal"),
        ("law-civil", "Law Civil"),
        ("law-criminal", "Law Criminal"),
    ]
    
    for ds_id, name in stores:
        create_data_store(ds_id, name)
