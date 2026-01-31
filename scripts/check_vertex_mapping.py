from google.cloud import discoveryengine_v1 as ds

def check_infra():
    project_id = "gen-lang-client-0464468580"
    location = "global"
    parent = f"projects/{project_id}/locations/{location}/collections/default_collection"
    
    print("--- 🔍 Data Stores ---")
    ds_client = ds.DataStoreServiceClient()
    for s in ds_client.list_data_stores(parent=parent):
        print(f"DS Display: {s.display_name} | ID: {s.name.split('/')[-1]}")
    
    print("\n--- 🔍 Search Engines (Apps) ---")
    e_client = ds.EngineServiceClient()
    for e in e_client.list_engines(parent=parent):
        ds_ids = [d.split('/')[-1] for d in e.data_store_ids]
        print(f"App: {e.display_name} | ID: {e.name.split('/')[-1]} | Linked Stores: {ds_ids}")

if __name__ == '__main__':
    check_infra()
